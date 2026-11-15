"""audit-log (support-ops) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("audit-log", "support-ops")


@app.get("/")
def root():
    return {"service": "audit-log", "domain": "support-ops", "status": "scaffold", "phase": 4}
