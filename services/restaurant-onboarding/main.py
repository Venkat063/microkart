"""restaurant-onboarding (catalog-merchants) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("restaurant-onboarding", "catalog-merchants")


@app.get("/")
def root():
    return {"service": "restaurant-onboarding", "domain": "catalog-merchants", "status": "scaffold", "phase": 2}
