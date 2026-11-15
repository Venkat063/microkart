#!/usr/bin/env bash
# Local Kubernetes test of the REAL chart: kind + in-cluster Postgres/Kafka, images built from source.
set -euo pipefail
cd "$(dirname "$0")/../.."
CLUSTER=microkart
kind get clusters | grep -qx "$CLUSTER" || kind create cluster --name "$CLUSTER"
for s in $(python scripts/matrix.py | python -c 'import sys,json;print(" ".join(json.load(sys.stdin)["service"]))'); do
  docker build -q -f docker/Dockerfile --build-arg SERVICE="$s" -t "microkart/$s:local" .
  kind load docker-image "microkart/$s:local" --name "$CLUSTER"
done
kubectl apply -f deploy/local/infra.yaml
kubectl -n microkart rollout status deploy/postgres deploy/kafka --timeout=180s
helm upgrade --install mk charts/microkart -n microkart -f deploy/local/values.yaml --wait --timeout 5m
echo "Ready. Run: scripts/ops/k8s-smoke.sh"
