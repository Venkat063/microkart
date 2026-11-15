"""service-registry (edge-platform) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("service-registry", "edge-platform")


@app.get("/")
def root():
    return {"service": "service-registry", "domain": "edge-platform", "status": "scaffold", "phase": 2}
