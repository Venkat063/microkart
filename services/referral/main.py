"""referral (users-accounts) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("referral", "users-accounts")


@app.get("/")
def root():
    return {"service": "referral", "domain": "users-accounts", "status": "scaffold", "phase": 2}
