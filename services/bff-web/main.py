"""bff-web (edge-platform) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("bff-web", "edge-platform")


@app.get("/")
def root():
    return {"service": "bff-web", "domain": "edge-platform", "status": "scaffold", "phase": 2}
