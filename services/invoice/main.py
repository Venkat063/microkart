"""invoice (payments-finance) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("invoice", "payments-finance")


@app.get("/")
def root():
    return {"service": "invoice", "domain": "payments-finance", "status": "scaffold", "phase": 3}
