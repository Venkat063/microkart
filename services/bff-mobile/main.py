"""bff-mobile (edge-platform) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("bff-mobile", "edge-platform")


@app.get("/")
def root():
    return {"service": "bff-mobile", "domain": "edge-platform", "status": "scaffold", "phase": 2}
