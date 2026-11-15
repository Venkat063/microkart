"""dispute-resolution (support-ops) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("dispute-resolution", "support-ops")


@app.get("/")
def root():
    return {"service": "dispute-resolution", "domain": "support-ops", "status": "scaffold", "phase": 4}
