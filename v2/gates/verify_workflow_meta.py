#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
m=json.loads((R/"v2/gates/development_method_contract.json").read_text())
w=(R/".github/workflows/cb6_development_gate.yml").read_text()
hpath=R/".github/workflows/cb6_hourly_development_cycle.yml"
err=[]
req=m["required_gate_scripts"]+m["required_regression_tests"]
for p in req:
 n=len(re.findall(r"(?<![A-Za-z0-9_./-])"+re.escape(p)+r"(?![A-Za-z0-9_./-])",w))
 if n!=1: err.append(f"{p}: workflow invocation count={n}, expected=1")
names=re.findall(r"^\s*- name:\s*(.+?)\s*$",w,re.M)
for n in sorted(set(names)):
 if names.count(n)>1: err.append(f"duplicate workflow step name: {n} count={names.count(n)}")
if not hpath.exists():
 err.append("hourly development workflow missing")
else:
 h=hpath.read_text()
 if not re.search(r"cron:\s*['\"]?[^'\"]*\*\s+\*\s+\*\s+\*['\"]?",h):
  err.append("hourly development workflow lacks hourly schedule")
 if "python3 v2/monitoring/verify_monitoring_policy.py" not in h:
  err.append("hourly development workflow lacks monitoring verifier")
# Development Auditor V2 runtime reachability must be structural, not a registry label.
if "pull_request:" not in w: err.append("Development Gate lacks pull_request reachability")
if "workflow_dispatch:" not in w: err.append("Development Gate lacks workflow_dispatch reachability")
if "push:" not in w: err.append("Development Gate lacks push reachability")
for rel in (".github/workflows/development_auditor_v2_runtime_candidate.yml",".github/workflows/development_auditor_v2_runtime_independent_review.yml"):
 p=R/rel
 if not p.exists(): err.append("Auditor runtime workflow missing: "+rel); continue
 s=p.read_text()
 if "workflow_dispatch:" not in s or "push:" not in s: err.append("Auditor runtime workflow lacks push/manual reachability: "+rel)
for p in (R/".github/workflows").glob("*.yml"):
 s=p.read_text()
 if "--require-feature-build" in s and "verify_project_gate.py" not in s:
  err.append("feature build bypasses common project gate: "+p.name)
pg=(R/"v2/gates/verify_project_gate.py").read_text()
if "verify_development_auditor_active_v2.py" not in pg: err.append("feature gate lacks Auditor V2 runtime blocking")
if err:
 print("CB6 WORKFLOW META FAIL:")
 for e in err: print(" -",e)
 raise SystemExit(1)
print(f"CB6 WORKFLOW META PASS: required={len(req)}; missing=0; duplicate_invocations=0; duplicate_step_names=0; hourly_monitoring=connected")
