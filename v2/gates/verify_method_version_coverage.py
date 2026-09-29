#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
METHOD=ROOT/"v2/gates/development_method_contract.json"
def fail(items):
 print("CB6 METHOD VERSION COVERAGE FAIL:")
 for x in items: print(" -",x)
 raise SystemExit(1)
m=json.loads(METHOD.read_text(encoding="utf-8"))
version=m.get("method_version")
if not isinstance(version,int) or version<1: fail(["central method_version missing/invalid"])
errors=[]
paths=sorted((ROOT/"v2/gates/features").glob("*.json"))
if not paths: errors.append("no feature contracts discovered")
for p in paths:
 try: d=json.loads(p.read_text(encoding="utf-8"))
 except Exception as e: errors.append(f"{p.relative_to(ROOT)} invalid JSON: {e}"); continue
 got=d.get("method_version")
 if got!=version: errors.append(f"{p.relative_to(ROOT)} method_version={got!r}, required={version}")
if errors: fail(errors)
print(f"CB6 METHOD VERSION COVERAGE PASS: method_version={version}; feature_contracts={len(paths)}")
