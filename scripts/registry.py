"""Loads services.yaml and assigns stable local ports (gateway=8000, others 8001+)."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load():
    data = yaml.safe_load((ROOT / "services.yaml").read_text())
    implemented = set(data["implemented"])
    out, port = [], 8001
    for domain, spec in data["domains"].items():
        for name in spec["services"]:
            if name == "api-gateway":
                p = 8000
            else:
                p, port = port, port + 1
            out.append({"name": name, "domain": domain, "port": p,
                        "implemented": name in implemented,
                        "phase": 1 if name in implemented else spec["phase"]})
    return out
