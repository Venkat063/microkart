"""demand-forecasting (data-intelligence) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("demand-forecasting", "data-intelligence")


@app.get("/")
def root():
    return {"service": "demand-forecasting", "domain": "data-intelligence", "status": "scaffold", "phase": 4}
