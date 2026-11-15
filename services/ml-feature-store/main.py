"""ml-feature-store (data-intelligence) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("ml-feature-store", "data-intelligence")


@app.get("/")
def root():
    return {"service": "ml-feature-store", "domain": "data-intelligence", "status": "scaffold", "phase": 4}
