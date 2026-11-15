"""ab-experimentation (data-intelligence) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("ab-experimentation", "data-intelligence")


@app.get("/")
def root():
    return {"service": "ab-experimentation", "domain": "data-intelligence", "status": "scaffold", "phase": 4}
