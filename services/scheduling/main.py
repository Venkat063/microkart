"""scheduling (ordering) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("scheduling", "ordering")


@app.get("/")
def root():
    return {"service": "scheduling", "domain": "ordering", "status": "scaffold", "phase": 2}
