"""address-book (users-accounts) - scaffold. Replace with real logic; keep create_app()."""
from microkart_common import create_app

app = create_app("address-book", "users-accounts")


@app.get("/")
def root():
    return {"service": "address-book", "domain": "users-accounts", "status": "scaffold", "phase": 2}
