"""surge-pricing (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("surge-pricing", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "surge-pricing", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
