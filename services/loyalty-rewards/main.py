"""loyalty-rewards (users-accounts) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("loyalty-rewards", "users-accounts")


@app.get("/")
def root():
    return {"service": "loyalty-rewards", "domain": "users-accounts", "status": "scaffold", "phase": 2}
