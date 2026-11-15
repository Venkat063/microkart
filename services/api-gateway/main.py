"""API Gateway: JWT verification, rate limiting, and routing to internal services."""
import os
import time
from collections import defaultdict, deque

import httpx
from fastapi import Request, Response
from microkart_common import create_app, read_token, service_url

app = create_app("api-gateway", "edge-platform")

# Only these services are reachable from outside. Payment is intentionally internal.
ROUTABLE = set(os.getenv("ROUTABLE", "auth-identity,user-profile,menu,cart,order,notification-orchestrator").split(","))
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "300"))
_hits: dict[str, deque] = defaultdict(deque)
_SKIP = {"host", "content-length", "x-user-id", "connection"}


def _is_public(service: str, path: str, method: str) -> bool:
    if service == "auth-identity" and path in ("register", "login"):
        return True
    return service == "menu" and method == "GET"


def _rate_limited(key: str) -> bool:
    now, window = time.time(), _hits[key]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        return True
    window.append(now)
    return False


@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in ROUTABLE:
        return Response('{"detail":"unknown service"}', 404, media_type="application/json")
    client_key = request.client.host if request.client else "unknown"
    if _rate_limited(client_key):
        return Response('{"detail":"rate limit exceeded"}', 429, media_type="application/json")

    headers = {k: v for k, v in request.headers.items() if k.lower() not in _SKIP}
    if not _is_public(service, path, request.method):
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return Response('{"detail":"missing bearer token"}', 401, media_type="application/json")
        claims = read_token(auth[7:])
        headers["x-user-id"] = claims["sub"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.request(request.method, f"{service_url(service)}/{path}",
                                     params=request.query_params, content=await request.body(),
                                     headers=headers)
    except httpx.HTTPError:
        return Response('{"detail":"upstream unavailable"}', 503, media_type="application/json")
    return Response(r.content, r.status_code, media_type=r.headers.get("content-type"))
