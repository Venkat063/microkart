"""checkout (ordering) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("checkout", "ordering")


@app.get("/")
def root():
    return {"service": "checkout", "domain": "ordering", "status": "scaffold", "phase": 2}
