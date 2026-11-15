"""in-app-chat-support (communication) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("in-app-chat-support", "communication")


@app.get("/")
def root():
    return {"service": "in-app-chat-support", "domain": "communication", "status": "scaffold", "phase": 3}
