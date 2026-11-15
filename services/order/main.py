"""Order: event-driven saga. POST /orders -> order.placed; Payment replies with payment.succeeded/failed.

order.placed (outbox) -> payment -> payment.succeeded|failed -> order status -> order.confirmed|failed
-> cart clears / notification fans out. Orders are 202 Accepted and move PENDING_PAYMENT -> CONFIRMED|PAYMENT_FAILED."""
import uuid

from fastapi import Header, HTTPException, Request
from pydantic import BaseModel
from microkart_common import Store, attach, call, create_app, current_user

app = create_app("order", "ordering")
store = Store("order")


class PlaceOrder(BaseModel):
    payment_method: str = "card"


@app.post("/orders", status_code=202)
async def place_order(body: PlaceOrder, request: Request, idempotency_key: str | None = Header(default=None)):
    uid = current_user(request)
    idem = f"{uid}:{idempotency_key}" if idempotency_key else None
    if idem and (existing := store.get("idem", idem)):
        return store.get("orders", existing)

    cart = await call("cart", "GET", "/cart", request=request, user_id=uid)
    if not cart["lines"]:
        raise HTTPException(422, "cart is empty")

    order = {"id": uuid.uuid4().hex[:12], "user_id": uid, "restaurant_id": cart["restaurant_id"],
             "lines": cart["lines"], "total": cart["total"], "status": "PENDING_PAYMENT"}
    with store.tx() as tx:  # order row + event commit atomically (outbox)
        tx.put("orders", order["id"], order)
        if idem:
            tx.put("idem", idem, order["id"])
        tx.emit("orders", "order.placed",
                {"order_id": order["id"], "user_id": uid, "amount": order["total"], "method": body.payment_method},
                key=order["id"], request_id=request.state.request_id)
    return order


@app.get("/orders")
def list_orders(request: Request):
    uid = current_user(request)
    return store.list("orders", lambda o: o["user_id"] == uid)


@app.get("/orders/{order_id}")
def get_order(order_id: str, request: Request):
    o = store.get("orders", order_id)
    if not o or o["user_id"] != current_user(request):
        raise HTTPException(404, "order not found")
    return o


def on_payment_succeeded(tx, data, event):
    o = tx.get("orders", data["order_id"])
    if not o or o["status"] != "PENDING_PAYMENT":
        return
    o.update(status="CONFIRMED", payment_id=data["payment_id"])
    tx.put("orders", o["id"], o)
    tx.emit("orders", "order.confirmed", {"order_id": o["id"], "user_id": o["user_id"], "total": o["total"]},
            key=o["id"], request_id=event.get("request_id"))


def on_payment_failed(tx, data, event):
    o = tx.get("orders", data["order_id"])
    if not o or o["status"] != "PENDING_PAYMENT":
        return
    o.update(status="PAYMENT_FAILED", payment_id=data["payment_id"])  # compensation: cart stays for retry
    tx.put("orders", o["id"], o)
    tx.emit("orders", "order.failed", {"order_id": o["id"], "user_id": o["user_id"], "reason": data.get("reason")},
            key=o["id"], request_id=event.get("request_id"))


attach(app, store, "order", {"payments": {"payment.succeeded": on_payment_succeeded,
                                            "payment.failed": on_payment_failed}})
