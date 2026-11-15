"""partner-earnings (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("partner-earnings", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "partner-earnings", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
