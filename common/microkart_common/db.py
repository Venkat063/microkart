"""Per-service persistence: a document store + transactional outbox on SQLAlchemy.
SQLite when DATABASE_URL is unset (local dev), PostgreSQL in compose/k8s. Same SQL for both."""
import contextlib
import json
import logging
import os
import time
import uuid
from pathlib import Path

from sqlalchemy import create_engine, event, text

log = logging.getLogger("db")
DATA_DIR = Path(os.getenv("DATA_DIR", ".data"))

DDL = [
    "CREATE TABLE IF NOT EXISTS kv (collection TEXT NOT NULL, id TEXT NOT NULL, doc TEXT NOT NULL, PRIMARY KEY (collection, id))",
    "CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, created DOUBLE PRECISION NOT NULL, topic TEXT NOT NULL, "
    "msg_key TEXT, payload TEXT NOT NULL, published INTEGER NOT NULL DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS processed (consumer TEXT NOT NULL, event_id TEXT NOT NULL, PRIMARY KEY (consumer, event_id))",
]


class Tx:
    """One database transaction. State changes and emit() commit or roll back together (outbox pattern)."""

    def __init__(self, conn):
        self.c = conn

    def put(self, coll: str, id_: str, doc: dict):
        self.c.execute(text("INSERT INTO kv (collection, id, doc) VALUES (:c, :i, :d) "
                            "ON CONFLICT (collection, id) DO UPDATE SET doc = excluded.doc"),
                       {"c": coll, "i": id_, "d": json.dumps(doc)})

    def get(self, coll: str, id_: str):
        row = self.c.execute(text("SELECT doc FROM kv WHERE collection=:c AND id=:i"), {"c": coll, "i": id_}).fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, coll: str, id_: str):
        self.c.execute(text("DELETE FROM kv WHERE collection=:c AND id=:i"), {"c": coll, "i": id_})

    def list(self, coll: str, where=None) -> list[dict]:
        rows = self.c.execute(text("SELECT doc FROM kv WHERE collection=:c ORDER BY id"), {"c": coll}).fetchall()
        docs = [json.loads(r[0]) for r in rows]
        return [d for d in docs if where(d)] if where else docs

    def emit(self, topic: str, type_: str, data: dict, key: str | None = None, request_id: str | None = None):
        event_ = {"id": uuid.uuid4().hex, "type": type_, "ts": time.time(), "data": data, "request_id": request_id}
        self.c.execute(text("INSERT INTO outbox (id, created, topic, msg_key, payload) VALUES (:i, :t, :tp, :k, :p)"),
                       {"i": event_["id"], "t": event_["ts"], "tp": topic, "k": key, "p": json.dumps(event_)})

    def first_time(self, consumer: str, event_id: str) -> bool:
        """Idempotent-consumer guard: True only the first time this consumer sees this event."""
        r = self.c.execute(text("INSERT INTO processed (consumer, event_id) VALUES (:c, :e) ON CONFLICT DO NOTHING"),
                           {"c": consumer, "e": event_id})
        return r.rowcount == 1


class Store:
    def __init__(self, service: str):
        url = os.getenv("DATABASE_URL")
        if not url:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{(DATA_DIR / (service + '.db')).resolve()}"
        sqlite = url.startswith("sqlite")
        self.engine = create_engine(url, **({"connect_args": {"timeout": 15}} if sqlite else {"pool_pre_ping": True}))
        if sqlite:
            @event.listens_for(self.engine, "connect")
            def _wal(dbapi_conn, _):
                dbapi_conn.execute("PRAGMA journal_mode=WAL")
        for attempt in range(30):  # database container may still be starting
            try:
                with self.engine.begin() as c:
                    for stmt in DDL:
                        c.execute(text(stmt))
                break
            except Exception as exc:
                if attempt == 29:
                    raise
                log.warning("database not ready (%s); retrying", type(exc).__name__)
                time.sleep(1)

    @contextlib.contextmanager
    def tx(self):
        with self.engine.begin() as c:
            yield Tx(c)

    def get(self, coll, id_):
        with self.tx() as t:
            return t.get(coll, id_)

    def put(self, coll, id_, doc):
        with self.tx() as t:
            t.put(coll, id_, doc)

    def delete(self, coll, id_):
        with self.tx() as t:
            t.delete(coll, id_)

    def list(self, coll, where=None):
        with self.tx() as t:
            return t.list(coll, where)

    def pending_outbox(self, limit=100):
        with self.engine.begin() as c:
            return c.execute(text("SELECT id, topic, msg_key, payload FROM outbox WHERE published=0 "
                                  "ORDER BY created LIMIT :n"), {"n": limit}).fetchall()

    def mark_published(self, id_: str):
        with self.engine.begin() as c:
            c.execute(text("UPDATE outbox SET published=1 WHERE id=:i"), {"i": id_})
