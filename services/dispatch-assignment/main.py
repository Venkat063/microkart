"""dispatch-assignment (logistics-delivery) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("dispatch-assignment", "logistics-delivery")


@app.get("/")
def root():
    return {"service": "dispatch-assignment", "domain": "logistics-delivery", "status": "scaffold", "phase": 3}
