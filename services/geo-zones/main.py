"""geo-zones (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("geo-zones", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "geo-zones", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
