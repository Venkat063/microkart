# MicroKart: 57-service food delivery + grocery platform

A microservices learning/portfolio project. All 57 services are registered in `services.yaml`.
**Phase 1 (8 services) is fully working end to end** with persistent storage, an event-driven order
saga (transactional outbox, idempotent consumers) and metrics/tracing; the other 49 are generated
scaffolds ready to be built out domain by domain.

## For DevOps

End-to-end infrastructure, GitOps and CI/CD live in **[docs/OPS.md](docs/OPS.md)**: Terraform (VPC, EKS, RDS, ECR, OIDC), Helm chart, ArgoCD app-of-apps, Strimzi Kafka, External Secrets, observability, promotion flow and alert runbooks. Start with `make validate && make kind-up && make k8s-smoke`.

## Quick start

```bash
make install
make run          # 8 Phase 1 services as local processes, gateway on :8000
make smoke        # 15 end-to-end checks through the gateway (saga is async, so it polls)
make test         # unit tests: outbox atomicity, idempotent consumer, bus ordering/offsets
# or with Docker (Postgres + Kafka + Prometheus + Grafana + Jaeger):
make up           # Phase 1 + infra  |  make up-all  # all 57 services
```

## Try it

```bash
curl -s localhost:8000/api/menu/restaurants
curl -s -XPOST localhost:8000/api/auth-identity/register -H 'content-type: application/json' -d '{"email":"a@b.com","password":"secret1"}'
TOKEN=$(curl -s -XPOST localhost:8000/api/auth-identity/login -H 'content-type: application/json' -d '{"email":"a@b.com","password":"secret1"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s -XPOST localhost:8000/api/cart/cart/items -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{"item_id":"i1","qty":2}'
curl -s -XPOST localhost:8000/api/order/orders -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{}'
```

Gateway routes are `/api/<service>/<path>`. Each service also serves Swagger at `/docs`.

## Layout

| Path | Purpose |
|---|---|
| `services.yaml` | Registry: domains, phases, which services are implemented |
| `services/<name>/main.py` | One FastAPI app per service |
| `common/microkart_common` | App factory, JWT, request-id propagation, inter-service `call()` with retries |
| `scripts/generate.py` | Scaffolds missing services, regenerates `docker-compose.yml` and Helm values |
| `docker/Dockerfile` | Single parameterised image build (`--build-arg SERVICE=...`) |
| `charts/microkart` | Helm chart (Deployment + Service per entry in values) |
| `.github/workflows/ci.yml` | Smoke test + per-service Docker build matrix |

## Adding a service

1. Edit `services/<name>/main.py` (keep `create_app(...)`).
2. Add the name to `implemented` in `services.yaml`; run `make generate`.
3. To expose it publicly, add it to `ROUTABLE` in the gateway.

## How the order saga works (Phase 2)

```
POST /orders -> Order: save order + outbox event in ONE transaction -> 202 PENDING_PAYMENT
  outbox relay -> topic `orders`: order.placed
  Payment (consumer): charge once per order -> payment.succeeded | payment.failed  (topic `payments`)
  Order (consumer): CONFIRMED + order.confirmed  |  PAYMENT_FAILED + order.failed
  Cart (consumer): clears on order.confirmed     Notification (consumer): records confirmed/failed
```

- **Outbox:** state change and event commit atomically; a relay publishes afterwards, so a broker outage never loses or invents events.
- **Idempotent consumers:** every handler runs in a transaction that first records `(consumer, event_id)`; redelivery is a no-op.
- **Retries and DLQ:** a failing handler retries 3 times, then the event goes to topic `dlq`.
- **Compensation:** a declined payment leaves the cart intact so the user can retry.
- **Bus:** `EVENT_BUS=local` (default) is a SQLite-backed log shared by local processes; `EVENT_BUS=kafka` uses Kafka (set automatically in compose).
- **Storage:** each service owns its database (SQLite locally, one Postgres database per service in compose). It is a JSON document store plus the outbox table, with the same SQL on both.

## Observability

Every service exposes Prometheus `/metrics` (HTTP rate/latency per route, events published/consumed per topic and type).
OpenTelemetry tracing turns on when `OTEL_EXPORTER_OTLP_ENDPOINT` is set (compose points it at Jaeger).
With `make up`: Grafana http://localhost:3000, Prometheus http://localhost:9090, Jaeger http://localhost:16686.

## Verification status

Verified locally in this repo: unit tests, and the 15-check smoke test on the local bus with SQLite.
**Not yet run:** the Docker images, `docker compose up`, the Postgres and Kafka code paths, and the Helm chart.
The Postgres path uses portable SQL (`ON CONFLICT`) and the Kafka path is a thin aiokafka wrapper, but expect to fix small things on first run.

## What is in Phase 1

Gateway (JWT check, rate limit, allow-listed routing, strips spoofed `x-user-id`), Auth (PBKDF2 + JWT),
User Profile, Menu, Cart (re-prices from Menu, one restaurant per cart), Order, Payment (mock gateway),
Notification (event-driven).

## Roadmap

- **Phase 2b:** build out Restaurant Onboarding (writes to Menu via events), Checkout, Promotions, Order Tracking, Address Book.
- **Phase 3:** payments/finance (wallet, refunds, settlement), logistics (dispatch, ETA, live location over WebSocket), notification channels.
- **Phase 4:** support/ops and data/ML services; ArgoCD GitOps and Terraform; Kubernetes rollout of the Helm chart.
