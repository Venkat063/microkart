"""Unit tests for the outbox, idempotent consumers and the local bus. Run: pytest -q"""
import asyncio
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ.pop("DATABASE_URL", None)
os.environ.pop("EVENT_BUS", None)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from microkart_common.db import Store
from microkart_common.events import LocalBus


def test_outbox_commits_atomically_with_state():
    s = Store("t1")
    try:
        with s.tx() as tx:
            tx.put("orders", "o1", {"x": 1})
            tx.emit("orders", "order.placed", {"id": "o1"})
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert s.get("orders", "o1") is None and s.pending_outbox() == []  # nothing leaked
    with s.tx() as tx:
        tx.put("orders", "o1", {"x": 1})
        tx.emit("orders", "order.placed", {"id": "o1"})
    assert s.get("orders", "o1") == {"x": 1} and len(s.pending_outbox()) == 1


def test_idempotent_consumer_guard():
    s = Store("t2")
    with s.tx() as tx:
        assert tx.first_time("payment", "evt-1") is True
    with s.tx() as tx:
        assert tx.first_time("payment", "evt-1") is False
        assert tx.first_time("cart", "evt-1") is True  # different consumer


def test_local_bus_delivers_in_order_and_resumes_from_offset():
    bus = LocalBus()
    got = []

    async def run():
        for i in range(3):
            await bus.publish("t", None, {"n": i})

        async def h(topic, ev):
            got.append(ev["n"])
        task = asyncio.create_task(bus.consume("g", ["t"], h))
        await asyncio.sleep(0.5)
        task.cancel()
        await bus.publish("t", None, {"n": 3})
        task = asyncio.create_task(bus.consume("g", ["t"], h))  # restarts at committed offset
        await asyncio.sleep(0.5)
        task.cancel()
    asyncio.run(run())
    assert got == [0, 1, 2, 3]
