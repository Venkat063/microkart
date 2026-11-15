"""order-tracking (ordering) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("order-tracking", "ordering")


@app.get("/")
def root():
    return {"service": "order-tracking", "domain": "ordering", "status": "scaffold", "phase": 2}
