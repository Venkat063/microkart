"""Payment: reacts to order.placed, charges via a mock gateway (method 'fail' declines), emits the outcome.
Idempotent by order id: a redelivered order.placed never charges twice."""
import uuid

from fastapi import HTTPException
from microkart_common import Store, attach, create_app

app = create_app("payment", "payments-finance")
store = Store("payment")


def on_order_placed(tx, data, event):
    if tx.get("charges", data["order_id"]):
        return
    declined = data["method"] == "fail" or data["amount"] > 10_000
    charge = {"id": uuid.uuid4().hex[:12], "order_id": data["order_id"], "user_id": data["user_id"],
              "amount": data["amount"], "method": data["method"], "status": "FAILED" if declined else "SUCCEEDED"}
    tx.put("charges", data["order_id"], charge)
    payload = {"order_id": data["order_id"], "payment_id": charge["id"], "user_id": data["user_id"],
               "amount": data["amount"]}
    if declined:
        tx.emit("payments", "payment.failed", {**payload, "reason": "declined"}, key=data["order_id"],
                request_id=event.get("request_id"))
    else:
        tx.emit("payments", "payment.succeeded", payload, key=data["order_id"], request_id=event.get("request_id"))


@app.get("/charges/{order_id}")
def get_charge(order_id: str):
    c = store.get("charges", order_id)
    if not c:
        raise HTTPException(404, "charge not found")
    return c


attach(app, store, "payment", {"orders": {"order.placed": on_order_placed}})
