"""Cart: one restaurant per cart; prices re-read from Menu. Clears itself when an order is confirmed."""
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field
from microkart_common import Store, attach, call, create_app, current_user

app = create_app("cart", "ordering")
store = Store("cart")


class AddItem(BaseModel):
    item_id: str
    qty: int = Field(1, ge=1, le=20)


async def _render(cart: dict | None, request: Request):
    if not cart or not cart["items"]:
        return {"restaurant_id": None, "lines": [], "total": 0}
    lines, total = [], 0
    for item_id, qty in cart["items"].items():
        it = await call("menu", "GET", f"/items/{item_id}", request=request)
        sub = it["price"] * qty
        total += sub
        lines.append({"item_id": item_id, "name": it["name"], "price": it["price"], "qty": qty, "subtotal": sub})
    return {"restaurant_id": cart["restaurant_id"], "lines": lines, "total": total}


@app.get("/cart")
async def get_cart(request: Request):
    return await _render(store.get("carts", current_user(request)), request)


@app.post("/cart/items")
async def add_item(body: AddItem, request: Request):
    uid = current_user(request)
    it = await call("menu", "GET", f"/items/{body.item_id}", request=request)
    cart = store.get("carts", uid) or {"restaurant_id": it["restaurant_id"], "items": {}}
    if cart["items"] and cart["restaurant_id"] != it["restaurant_id"]:
        raise HTTPException(409, "cart already has items from another restaurant; clear it first")
    cart["restaurant_id"] = it["restaurant_id"]
    cart["items"][body.item_id] = cart["items"].get(body.item_id, 0) + body.qty
    store.put("carts", uid, cart)
    return await _render(cart, request)


@app.delete("/cart")
def clear_cart(request: Request):
    store.delete("carts", current_user(request))
    return {"cleared": True}


def on_order_confirmed(tx, data, event):
    tx.delete("carts", data["user_id"])


attach(app, store, "cart", {"orders": {"order.confirmed": on_order_confirmed}})
