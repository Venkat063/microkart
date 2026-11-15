"""refund (payments-finance) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("refund", "payments-finance")


@app.get("/")
def root():
    return {"service": "refund", "domain": "payments-finance", "status": "scaffold", "phase": 3}
