"""event-ingestion (data-intelligence) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("event-ingestion", "data-intelligence")


@app.get("/")
def root():
    return {"service": "event-ingestion", "domain": "data-intelligence", "status": "scaffold", "phase": 4}
