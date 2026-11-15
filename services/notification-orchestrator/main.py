"""Notification Orchestrator: turns order events into user notifications (Email/SMS/Push fan-out in Phase 3)."""
import time
import uuid

from fastapi import Request
from pydantic import BaseModel
from microkart_common import Store, attach, create_app, current_user

app = create_app("notification-orchestrator", "communication")
store = Store("notification-orchestrator")


class Notify(BaseModel):
    user_id: str
    type: str
    message: str


def _record(tx, user_id: str, kind: str, message: str):
    tx.put("inbox", f"{time.time():.6f}-{uuid.uuid4().hex[:6]}",
           {"user_id": user_id, "type": kind, "message": message, "ts": int(time.time())})


@app.post("/notify", status_code=202)
def notify(n: Notify):
    with store.tx() as tx:
        _record(tx, n.user_id, n.type, n.message)
    return {"queued": True}


@app.get("/notifications")
def mine(request: Request):
    uid = current_user(request)
    return store.list("inbox", lambda d: d["user_id"] == uid)


def on_confirmed(tx, data, event):
    _record(tx, data["user_id"], "order_confirmed", f"Order {data['order_id']} confirmed (Rs {data['total']})")


def on_failed(tx, data, event):
    _record(tx, data["user_id"], "order_failed", f"Payment failed for order {data['order_id']}")


attach(app, store, "notification-orchestrator",
       {"orders": {"order.confirmed": on_confirmed, "order.failed": on_failed}})
