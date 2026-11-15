"""promotions-coupons (ordering) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("promotions-coupons", "ordering")


@app.get("/")
def root():
    return {"service": "promotions-coupons", "domain": "ordering", "status": "scaffold", "phase": 2}
