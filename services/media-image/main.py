"""media-image (catalog-merchants) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("media-image", "catalog-merchants")


@app.get("/")
def root():
    return {"service": "media-image", "domain": "catalog-merchants", "status": "scaffold", "phase": 2}
