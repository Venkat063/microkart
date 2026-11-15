"""User Profile: per-user display data."""
from fastapi import Request
from pydantic import BaseModel
from microkart_common import Store, create_app, current_user

app = create_app("user-profile", "users-accounts")
store = Store("user-profile")


class Profile(BaseModel):
    name: str = ""
    phone: str = ""


@app.get("/me")
def get_me(request: Request):
    uid = current_user(request)
    return {"user_id": uid, **(store.get("profiles", uid) or Profile().model_dump())}


@app.put("/me")
def put_me(p: Profile, request: Request):
    uid = current_user(request)
    store.put("profiles", uid, p.model_dump())
    return {"user_id": uid, **p.model_dump()}
