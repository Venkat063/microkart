"""subscription (ordering) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("subscription", "ordering")


@app.get("/")
def root():
    return {"service": "subscription", "domain": "ordering", "status": "scaffold", "phase": 2}
