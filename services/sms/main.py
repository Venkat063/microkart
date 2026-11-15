"""sms (communication) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("sms", "communication")


@app.get("/")
def root():
    return {"service": "sms", "domain": "communication", "status": "scaffold", "phase": 3}
