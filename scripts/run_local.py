"""Runs services as local uvicorn processes (no Docker). Usage: run_local.py [phase1|all|name ...]"""
import json, os, signal, subprocess, sys, time
from registry import ROOT, load

services = load()
arg = sys.argv[1:] or ["phase1"]
if arg == ["all"]:
    chosen = services
elif arg == ["phase1"]:
    chosen = [s for s in services if s["phase"] == 1]
else:
    chosen = [s for s in services if s["name"] in arg]

env = {**os.environ, "SERVICE_PORTS_JSON": json.dumps({s["name"]: s["port"] for s in services}),
       "PYTHONPATH": str(ROOT / "common"), "DATA_DIR": str(ROOT / ".data")}
(ROOT / ".logs").mkdir(exist_ok=True)
procs = []
for s in chosen:
    log = open(ROOT / ".logs" / f"{s['name']}.log", "w")
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "--app-dir", str(ROOT / "services" / s["name"]),
         "main:app", "--port", str(s["port"]), "--log-level", "warning"],
        env=env, stdout=log, stderr=log))
    print(f"started {s['name']:<28} http://127.0.0.1:{s['port']}")
print("\nGateway: http://127.0.0.1:8000  (Ctrl+C to stop)")


def stop(*_):
    for p in procs:
        p.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
while True:
    time.sleep(1)
