"""feature-flags (support-ops) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("feature-flags", "support-ops")


@app.get("/")
def root():
    return {"service": "feature-flags", "domain": "support-ops", "status": "scaffold", "phase": 4}
