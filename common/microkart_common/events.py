"""Event bus + outbox relay + idempotent consumers.
EVENT_BUS=local (default): SQLite-backed log shared by processes on one machine, no Kafka needed.
EVENT_BUS=kafka: aiokafka against KAFKA_BOOTSTRAP. Consumers get at-least-once delivery;
the `processed` table makes handlers effectively exactly-once."""
import asyncio
import json
import logging
import os
import sqlite3

from . import metrics
from .db import DATA_DIR

log = logging.getLogger("events")
MAX_ATTEMPTS = 3


class LocalBus:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.path = str((DATA_DIR / "bus.db").resolve())
        with self._conn() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("CREATE TABLE IF NOT EXISTS log (seq INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, payload TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS offsets (grp TEXT, topic TEXT, seq INTEGER, PRIMARY KEY (grp, topic))")

    def _conn(self):
        return sqlite3.connect(self.path, timeout=15)

    async def start(self):
        pass

    async def publish(self, topic, key, event):
        with self._conn() as c:
            c.execute("INSERT INTO log (topic, payload) VALUES (?, ?)", (topic, json.dumps(event)))

    async def consume(self, group, topics, handler):
        while True:
            busy = False
            for topic in topics:
                with self._conn() as c:
                    row = c.execute("SELECT seq FROM offsets WHERE grp=? AND topic=?", (group, topic)).fetchone()
                    last = row[0] if row else 0
                    rows = c.execute("SELECT seq, payload FROM log WHERE topic=? AND seq>? ORDER BY seq LIMIT 50",
                                     (topic, last)).fetchall()
                for seq, payload in rows:
                    busy = True
                    await handler(topic, json.loads(payload))
                    with self._conn() as c:
                        c.execute("INSERT INTO offsets (grp, topic, seq) VALUES (?,?,?) "
                                  "ON CONFLICT (grp, topic) DO UPDATE SET seq=excluded.seq", (group, topic, seq))
            if not busy:
                await asyncio.sleep(0.1)


class KafkaBus:
    def __init__(self):
        self.bootstrap = os.environ["KAFKA_BOOTSTRAP"]
        self.producer = None

    async def start(self):
        from aiokafka import AIOKafkaProducer
        while True:
            try:
                self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap)
                await self.producer.start()
                return
            except Exception as exc:
                log.warning("kafka producer not ready (%s); retrying", exc)
                await asyncio.sleep(2)

    async def publish(self, topic, key, event):
        await self.producer.send_and_wait(topic, json.dumps(event).encode(), key=key.encode() if key else None)

    async def consume(self, group, topics, handler):
        from aiokafka import AIOKafkaConsumer
        while True:
            consumer = AIOKafkaConsumer(*topics, bootstrap_servers=self.bootstrap, group_id=group,
                                        enable_auto_commit=False, auto_offset_reset="earliest")
            try:
                await consumer.start()
                async for msg in consumer:
                    await handler(msg.topic, json.loads(msg.value))
                    await consumer.commit()
            except Exception as exc:
                log.warning("kafka consumer error (%s); restarting", exc)
                await asyncio.sleep(2)
            finally:
                await consumer.stop()


def get_bus():
    return KafkaBus() if os.getenv("EVENT_BUS", "local") == "kafka" else LocalBus()


def attach(app, store, service: str, subscriptions: dict[str, dict] | None = None):
    """Wire background workers into the app: outbox relay, plus consumers for
    subscriptions = {topic: {event_type: handler(tx, data, event)}}."""
    bus = get_bus()

    async def relay():
        await bus.start()
        while True:
            rows = await asyncio.to_thread(store.pending_outbox)
            for id_, topic, key, payload in rows:
                try:
                    ev = json.loads(payload)
                    await bus.publish(topic, key, ev)
                    await asyncio.to_thread(store.mark_published, id_)
                    metrics.EVENTS_PUBLISHED.labels(service, topic, ev["type"]).inc()
                except Exception as exc:  # broker down: leave in outbox, retry
                    log.warning("publish failed (%s); will retry", exc)
                    await asyncio.sleep(1)
                    break
            if not rows:
                await asyncio.sleep(0.1)

    app.state.workers.append(relay)
    if not subscriptions:
        return

    async def on_message(topic, ev):
        handler = subscriptions.get(topic, {}).get(ev["type"])
        if not handler:
            return
        for attempt in range(MAX_ATTEMPTS):
            try:
                def run():
                    with store.tx() as tx:
                        if not tx.first_time(service, ev["id"]):
                            return "duplicate"
                        handler(tx, ev["data"], ev)
                        return "ok"
                result = await asyncio.to_thread(run)
                metrics.EVENTS_CONSUMED.labels(service, topic, ev["type"], result).inc()
                return
            except Exception:
                log.exception("handler %s failed (attempt %d)", ev["type"], attempt + 1)
                await asyncio.sleep(0.2 * (attempt + 1))
        metrics.EVENTS_CONSUMED.labels(service, topic, ev["type"], "dead_letter").inc()
        try:
            await bus.publish("dlq", ev["id"], {"service": service, "topic": topic, "event": ev})
        except Exception:
            log.error("could not dead-letter event %s", ev["id"])

    async def consumer():
        await bus.consume(service, list(subscriptions), on_message)

    app.state.workers.append(consumer)
