"""fleet-management (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("fleet-management", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "fleet-management", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
