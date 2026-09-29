#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
m=json.loads((R/"v2/gates/development_method_contract.json").read_text())
w=(R/".github/workflows/cb6_development_gate.yml").read_text()
req=m["required_gate_scripts"]+m["required_regression_tests"]
err=[]
for p in req:
 n=len(re.findall(r"(?<![A-Za-z0-9_./-])"+re.escape(p)+r"(?![A-Za-z0-9_./-])",w))
 if n!=1: err.append(f"{p}: workflow invocation count={n}, expected=1")
names=re.findall(r"^\s*- name:\s*(.+?)\s*$",w,re.M)
for n in sorted(set(names)):
 if names.count(n)>1: err.append(f"duplicate workflow step name: {n} count={names.count(n)}")
if err:
 print("CB6 WORKFLOW META FAIL:")
 for e in err: print(" -",e)
 raise SystemExit(1)
print(f"CB6 WORKFLOW META PASS: required={len(req)}; missing=0; duplicate_invocations=0; duplicate_step_names=0")
