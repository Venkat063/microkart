"""End-to-end check through the gateway. Usage: python tests/smoke_test.py [gateway_url]"""
import sys, time, uuid
import httpx

GW = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
c = httpx.Client(base_url=GW + "/api", timeout=10)


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        sys.exit(1)


def wait_for(fn, timeout=10):
    """Poll until fn() returns a truthy value (the saga is asynchronous)."""
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(0.2)
    return None


email = f"user{uuid.uuid4().hex[:6]}@example.com"
ok(c.post("/auth-identity/register", json={"email": email, "password": "secret1"}).status_code == 201, "register")
tok = c.post("/auth-identity/login", json={"email": email, "password": "secret1"}).json()["access_token"]
auth = {"Authorization": f"Bearer {tok}"}

ok(c.get("/cart/cart").status_code == 401, "cart rejects anonymous requests")
ok(c.get("/payment/charges/x", headers=auth).status_code == 404, "payment is not exposed via gateway")
ok(len(c.get("/menu/restaurants").json()) == 3, "public menu browsing")

c.put("/user-profile/me", json={"name": "Asha", "phone": "9999999999"}, headers=auth)
ok(c.get("/user-profile/me", headers=auth).json()["name"] == "Asha", "profile round-trip")

c.post("/cart/cart/items", json={"item_id": "i3", "qty": 2}, headers=auth)
cart = c.post("/cart/cart/items", json={"item_id": "i4"}, headers=auth).json()
ok(cart["total"] == 560, "cart total from Menu prices (2x260 + 40)")
ok(c.post("/cart/cart/items", json={"item_id": "i1"}, headers=auth).status_code == 409, "one restaurant per cart")

key = {"Idempotency-Key": uuid.uuid4().hex, **auth}
r = c.post("/order/orders", json={}, headers=key)
order = r.json()
ok(r.status_code == 202 and order["status"] == "PENDING_PAYMENT", "order accepted (202) and pending payment")
ok(c.post("/order/orders", json={}, headers=key).json()["id"] == order["id"], "idempotent retry returns same order")
final = wait_for(lambda: (o := c.get(f"/order/orders/{order['id']}", headers=auth).json())["status"] != "PENDING_PAYMENT" and o)
ok(final and final["status"] == "CONFIRMED", "saga: payment succeeded -> order CONFIRMED")
ok(wait_for(lambda: c.get("/cart/cart", headers=auth).json()["lines"] == []), "cart cleared by order.confirmed event")
ok(wait_for(lambda: any(n["type"] == "order_confirmed" for n in
                        c.get("/notification-orchestrator/notifications", headers=auth).json())),
   "notification created from order.confirmed event")

c.post("/cart/cart/items", json={"item_id": "i5"}, headers=auth)
failed = c.post("/order/orders", json={"payment_method": "fail"}, headers=auth).json()
f = wait_for(lambda: (o := c.get(f"/order/orders/{failed['id']}", headers=auth).json())["status"] != "PENDING_PAYMENT" and o)
ok(f and f["status"] == "PAYMENT_FAILED", "saga: declined payment -> PAYMENT_FAILED")
ok(len(c.get("/cart/cart", headers=auth).json()["lines"]) == 1, "cart kept after failed payment for retry")
ok(wait_for(lambda: any(n["type"] == "order_failed" for n in
                        c.get("/notification-orchestrator/notifications", headers=auth).json())),
   "failure notification created")
print("\nAll checks passed.")
