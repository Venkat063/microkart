"""config-service (edge-platform) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("config-service", "edge-platform")


@app.get("/")
def root():
    return {"service": "config-service", "domain": "edge-platform", "status": "scaffold", "phase": 2}
