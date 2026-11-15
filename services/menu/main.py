"""Menu: restaurants and items. Seeded on first start; Restaurant Onboarding will own writes in Phase 2b."""
from fastapi import HTTPException
from microkart_common import Store, create_app

app = create_app("menu", "catalog-merchants")
store = Store("menu")

SEED_RESTAURANTS = [
    {"id": "r1", "name": "Dosa Corner", "cuisine": "South Indian"},
    {"id": "r2", "name": "Biryani House", "cuisine": "Hyderabadi"},
    {"id": "r3", "name": "Green Bowl", "cuisine": "Healthy"},
]
SEED_ITEMS = [
    {"id": "i1", "restaurant_id": "r1", "name": "Masala Dosa", "price": 90},
    {"id": "i2", "restaurant_id": "r1", "name": "Filter Coffee", "price": 40},
    {"id": "i3", "restaurant_id": "r2", "name": "Chicken Biryani", "price": 260},
    {"id": "i4", "restaurant_id": "r2", "name": "Raita", "price": 40},
    {"id": "i5", "restaurant_id": "r3", "name": "Quinoa Salad", "price": 220},
]
if not store.list("restaurants"):
    with store.tx() as tx:
        for r in SEED_RESTAURANTS:
            tx.put("restaurants", r["id"], r)
        for i in SEED_ITEMS:
            tx.put("items", i["id"], i)


@app.get("/restaurants")
def restaurants():
    return store.list("restaurants")


@app.get("/restaurants/{rid}/menu")
def restaurant_menu(rid: str):
    if not store.get("restaurants", rid):
        raise HTTPException(404, "restaurant not found")
    return store.list("items", lambda i: i["restaurant_id"] == rid)


@app.get("/items/{item_id}")
def item(item_id: str):
    it = store.get("items", item_id)
    if not it:
        raise HTTPException(404, "item not found")
    return it
