"""Prints the CI build matrix (implemented services) as JSON: {"service": [...]}"""
import json
from registry import load

print(json.dumps({"service": [s["name"] for s in load() if s["implemented"]]}))
