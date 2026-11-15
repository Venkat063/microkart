# Applied once per cluster by scripts/ops/bootstrap-cluster.sh (envsubst fills ENV and REPO_URL).
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root
  namespace: argocd
spec:
  project: default
  source:
    repoURL: ${REPO_URL}
    targetRevision: ${REVISION}
    path: deploy/argocd/apps
    helm:
      valueFiles: [../../envs/${ENV}/apps.yaml]
      parameters:
        - {name: env, value: ${ENV}}
        - {name: repoURL, value: ${REPO_URL}}
        - {name: targetRevision, value: ${REVISION}}
  destination: {server: https://kubernetes.default.svc, namespace: argocd}
  syncPolicy:
    automated: {prune: true, selfHeal: true}
