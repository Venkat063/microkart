#!/usr/bin/env bash
# Installs ArgoCD into the current cluster and hands control to GitOps (root app-of-apps).
# Usage: REPO_URL=git@github.com:ORG/microkart.git scripts/ops/bootstrap-cluster.sh <dev|staging|prod>
set -euo pipefail
ENV="${1:?usage: bootstrap-cluster.sh <dev|staging|prod>}"
: "${REPO_URL:?set REPO_URL (the git URL ArgoCD will watch)}"
REVISION="${REVISION:-main}"
ARGOCD_CHART_VERSION="${ARGOCD_CHART_VERSION:-7.7.5}"
cd "$(dirname "$0")/../.."

echo ">> context: $(kubectl config current-context)  env: $ENV"
read -r -p "Bootstrap ArgoCD on THIS cluster? [y/N] " ok; [[ "$ok" == "y" ]] || exit 1

helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update argo >/dev/null
helm upgrade --install argocd argo/argo-cd -n argocd --create-namespace --version "$ARGOCD_CHART_VERSION" --wait --timeout 10m

# Private repo: provide a read-only deploy key (GitHub repo -> Settings -> Deploy keys).
if [[ -n "${GIT_DEPLOY_KEY_FILE:-}" ]]; then
  kubectl -n argocd create secret generic repo-microkart \
    --from-literal=type=git --from-literal=url="$REPO_URL" \
    --from-file=sshPrivateKey="$GIT_DEPLOY_KEY_FILE" --dry-run=client -o yaml \
    | kubectl label --local -f - argocd.argoproj.io/secret-type=repository -o yaml | kubectl apply -f -
fi

export ENV REPO_URL REVISION
envsubst < deploy/argocd/root-app.yaml.tpl | kubectl apply -f -

cat <<MSG

ArgoCD is up and syncing '$ENV'. Next:
  kubectl -n argocd get applications -w
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
  kubectl -n argocd port-forward svc/argocd-server 8080:443      # https://localhost:8080  (user: admin)
MSG
