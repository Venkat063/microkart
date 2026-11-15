.PHONY: test clean install generate run run-all smoke up up-all down helm-lint
install:   ; pip install -r requirements-dev.txt
generate:  ; python scripts/generate.py
run:       ; rm -rf .data && python scripts/run_local.py phase1
run-all:   ; python scripts/run_local.py all
smoke:     ; python tests/smoke_test.py
up:        ; docker compose up --build
up-all:    ; docker compose --profile all up --build
down:      ; docker compose --profile all down
helm-lint: ; helm lint charts/microkart
test:      ; python -m pytest -q tests/test_store_events.py
clean:     ; rm -rf .data .logs

# ---- ops
.PHONY: validate kind-up kind-down k8s-smoke tf-fmt
validate:   ; scripts/ops/validate.sh
kind-up:    ; scripts/ops/kind-up.sh
kind-down:  ; kind delete cluster --name microkart
k8s-smoke:  ; scripts/ops/k8s-smoke.sh
tf-fmt:     ; terraform fmt -recursive terraform
