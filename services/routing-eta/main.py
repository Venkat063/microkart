"""routing-eta (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("routing-eta", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "routing-eta", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
