"""live-location (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("live-location", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "live-location", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
