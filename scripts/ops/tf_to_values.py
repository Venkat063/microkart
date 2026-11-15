#!/usr/bin/env python3
"""Copy Terraform outputs into the GitOps values files so nothing is typed by hand.
Usage: scripts/ops/tf_to_values.py <dev|staging|prod>      (TF=tofu to use OpenTofu)
Run `terraform workspace`-free: it reads whatever state the env's backend config points at."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TF = os.getenv("TF", "terraform")


def tf_output(chdir: str) -> dict:
    out = subprocess.run([TF, f"-chdir={ROOT / chdir}", "output", "-json"], check=True, capture_output=True, text=True)
    return {k: v["value"] for k, v in json.loads(out.stdout).items()}


def main():
    env = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    if env not in ("dev", "staging", "prod"):
        sys.exit("env must be dev, staging or prod")
    boot, stack = tf_output("terraform/bootstrap"), tf_output("terraform")
    d = ROOT / "deploy" / "envs" / env
    header = "# Written by scripts/ops/tf_to_values.py from `terraform output`. Do not edit by hand.\n"
    (d / "generated.yaml").write_text(f"{header}image:\n  registry: {boot['ecr_registry']}\n")
    (d / "external-secrets.yaml").write_text(
        f"{header}serviceAccount:\n  annotations:\n    eks.amazonaws.com/role-arn: {stack['eso_role_arn']}\n")
    print(f"updated deploy/envs/{env}/generated.yaml and external-secrets.yaml")
    print(f"cluster: {stack['cluster_name']}   rds: {stack['rds_endpoint']}")


if __name__ == "__main__":
    main()
