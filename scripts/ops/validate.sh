#!/usr/bin/env bash
# Static validation of everything an ops engineer ships: charts render and match K8s/CRD schemas,
# Terraform is formatted. Needs helm + kubeconform (+ terraform or tofu for the fmt check).
set -euo pipefail
cd "$(dirname "$0")/../.."
KC=(kubeconform -strict -summary -ignore-missing-schemas -kubernetes-version "${K8S_VERSION:-1.31.0}"
    -schema-location default
    -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json')

python scripts/generate.py >/dev/null
git rev-parse --git-dir >/dev/null 2>&1 && { git diff --quiet -- charts/microkart/services.yaml docker-compose.yml infra || echo "WARN: generated files differ from git (run make generate and commit)"; }

for e in dev staging prod; do
  V=(-f deploy/envs/$e/microkart.yaml -f deploy/envs/$e/generated.yaml -f deploy/envs/$e/image-tag.yaml)
  helm lint charts/microkart "${V[@]}" >/dev/null
  echo -n "microkart/$e:        "; helm template mk charts/microkart -n microkart "${V[@]}" | "${KC[@]}" | tail -1
  echo -n "platform-config/$e:  "; helm template pc deploy/platform/config -f deploy/envs/$e/platform-config.yaml | "${KC[@]}" | tail -1
  echo -n "argocd-apps/$e:      "; helm template root deploy/argocd/apps -f deploy/envs/$e/apps.yaml --set env=$e | "${KC[@]}" | tail -1
done
echo -n "local:              "; helm template mk charts/microkart -n microkart -f deploy/local/values.yaml | "${KC[@]}" | tail -1
echo -n "local-infra:        "; kubeconform -strict -summary -kubernetes-version "${K8S_VERSION:-1.31.0}" deploy/local/infra.yaml | tail -1

TF="$(command -v terraform || command -v tofu || true)"
if [[ -n "$TF" ]]; then "$TF" fmt -check -recursive terraform && echo "terraform fmt: clean"; else echo "terraform/tofu not installed: skipped fmt"; fi
echo "OK"
