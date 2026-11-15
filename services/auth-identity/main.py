"""Auth/Identity: registration, login, token issuance. Persisted in its own database."""
import hashlib
import os
import uuid

from fastapi import HTTPException
from pydantic import BaseModel
from microkart_common import Store, create_app, make_token

app = create_app("auth-identity", "edge-platform")
store = Store("auth-identity")


class Credentials(BaseModel):
    email: str
    password: str


def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()


@app.post("/register", status_code=201)
def register(c: Credentials):
    email = c.email.lower().strip()
    if "@" not in email or len(c.password) < 6:
        raise HTTPException(422, "valid email and password (6+ chars) required")
    if store.get("users", email):
        raise HTTPException(409, "email already registered")
    salt = os.urandom(16)
    user = {"id": uuid.uuid4().hex[:12], "salt": salt.hex(), "hash": _hash(c.password, salt)}
    store.put("users", email, user)
    return {"user_id": user["id"], "email": email}


@app.post("/login")
def login(c: Credentials):
    u = store.get("users", c.email.lower().strip())
    if not u or _hash(c.password, bytes.fromhex(u["salt"])) != u["hash"]:
        raise HTTPException(401, "invalid credentials")
    return {"access_token": make_token(u["id"]), "token_type": "bearer", "user_id": u["id"]}
