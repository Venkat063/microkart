"""Shared building blocks for every MicroKart service."""
import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import metrics
from .db import Store
from .events import attach

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")


def _setup_tracing(app: FastAPI, name: str):
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        provider = TracerProvider(resource=Resource.create({"service.name": name}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
    except Exception as exc:  # tracing must never take a service down
        logging.getLogger(name).warning("tracing disabled: %s", exc)


def create_app(name: str, domain: str = "", description: str = "") -> FastAPI:
    """App factory: request-id propagation, access logs, Prometheus /metrics, tracing,
    /health, /info, and background workers (outbox relay, event consumers)."""
    log = logging.getLogger(name)
    started = time.time()

    @asynccontextmanager
    async def lifespan(app_: FastAPI):
        tasks = [asyncio.create_task(w()) for w in app_.state.workers]
        yield
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title=name, description=description, lifespan=lifespan)
    app.state.workers = []

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - t0
        route = getattr(request.scope.get("route"), "path", "unmatched")
        response.headers["x-request-id"] = rid
        if route != "/metrics":
            metrics.HTTP_REQUESTS.labels(name, request.method, route, response.status_code).inc()
            metrics.HTTP_LATENCY.labels(name, route).observe(elapsed)
            log.info("%s %s -> %s %.1fms rid=%s", request.method, request.url.path,
                     response.status_code, elapsed * 1000, rid)
        return response

    @app.get("/health", tags=["ops"])
    def health():
        return {"status": "ok", "service": name}

    @app.get("/info", tags=["ops"])
    def info():
        return {"service": name, "domain": domain, "uptime_s": round(time.time() - started, 1)}

    @app.get("/metrics", tags=["ops"], include_in_schema=False)
    def prom():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    _setup_tracing(app, name)
    return app


def service_url(service: str) -> str:
    ports = os.getenv("SERVICE_PORTS_JSON")  # set by scripts/run_local.py
    if ports:
        return f"http://127.0.0.1:{json.loads(ports)[service]}"
    return f"http://{service}:8000"  # docker-compose / k8s DNS


def make_token(user_id: str, ttl_s: int = 3600) -> str:
    now = int(time.time())
    return jwt.encode({"sub": user_id, "iat": now, "exp": now + ttl_s}, JWT_SECRET, JWT_ALG)


def read_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError as exc:
        raise HTTPException(401, f"invalid token: {exc}")


def current_user(request: Request) -> str:
    """User id injected by the gateway after token verification."""
    uid = request.headers.get("x-user-id")
    if not uid:
        raise HTTPException(401, "missing user context")
    return uid


async def call(service: str, method: str, path: str, *, request: Request | None = None,
               user_id: str | None = None, json_body=None, headers: dict | None = None,
               timeout: float = 3.0, retries: int = 2):
    """Service-to-service HTTP call with request-id propagation and retry on connect errors."""
    h = dict(headers or {})
    if request is not None and getattr(request.state, "request_id", None):
        h["x-request-id"] = request.state.request_id
    if user_id:
        h["x-user-id"] = user_id
    last = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.request(method, service_url(service) + path, json=json_body, headers=h)
            break
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            last = exc
            if attempt == retries:
                raise HTTPException(503, f"{service} unavailable")
            await asyncio.sleep(0.1 * (attempt + 1))
        except httpx.TimeoutException:
            raise HTTPException(504, f"{service} timed out")
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise HTTPException(r.status_code, detail)
    return r.json()
