"""preferences (users-accounts) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("preferences", "users-accounts")


@app.get("/")
def root():
    return {"service": "preferences", "domain": "users-accounts", "status": "scaffold", "phase": 2}
