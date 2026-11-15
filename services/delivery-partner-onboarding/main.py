"""delivery-partner-onboarding (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("delivery-partner-onboarding", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "delivery-partner-onboarding", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
