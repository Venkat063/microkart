"""admin-console (support-ops) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("admin-console", "support-ops")


@app.get("/")
def root():
    return {"service": "admin-console", "domain": "support-ops", "status": "scaffold", "phase": 4}
