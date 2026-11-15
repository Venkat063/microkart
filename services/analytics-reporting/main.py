"""analytics-reporting (data-intelligence) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("analytics-reporting", "data-intelligence")


@app.get("/")
def root():
    return {"service": "analytics-reporting", "domain": "data-intelligence", "status": "scaffold", "phase": 4}
