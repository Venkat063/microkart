#!/usr/bin/env bash
# Runs the end-to-end smoke test against a cluster via port-forward. Usage: k8s-smoke.sh [namespace]
set -euo pipefail
cd "$(dirname "$0")/../.."
NS="${1:-microkart}"
kubectl -n "$NS" port-forward svc/api-gateway 18000:8000 >/dev/null 2>&1 &
PF=$!; trap 'kill $PF 2>/dev/null' EXIT
for _ in $(seq 1 30); do curl -sf localhost:18000/health >/dev/null && break; sleep 1; done
python tests/smoke_test.py http://127.0.0.1:18000
