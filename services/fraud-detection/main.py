"""fraud-detection (payments-finance) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("fraud-detection", "payments-finance")


@app.get("/")
def root():
    return {"service": "fraud-detection", "domain": "payments-finance", "status": "scaffold", "phase": 3}
