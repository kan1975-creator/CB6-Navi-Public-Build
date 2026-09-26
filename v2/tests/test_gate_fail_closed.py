#!/usr/bin/env python3
"""Destructive tests for CB6 gate invariants using isolated repository copies."""
import json, shutil, subprocess, tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
CASES=[]

def mutate_missing_trace(r):
 p=r/"v2/gates/traceability.json"; d=json.loads(p.read_text()); d["traces"]=[x for x in d["traces"] if x["decision_id"]!="SIG-200M-001"]; p.write_text(json.dumps(d))
CASES.append(("missing-active-decision", mutate_missing_trace, "active decisions absent from traceability"))

def mutate_bypass(r):
 p=r/".github/workflows/test_bypass.yml"; p.write_text("""name: bypass
on:
  push:
    branches: [cb6-v2-clean]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: ./gradlew assemble
""")
CASES.append(("gate-less-workflow", mutate_bypass, "workflow bypasses feature gate"))

def mutate_superseded(r):
 p=r/"v2/gates/traceability.json"; d=json.loads(p.read_text())
 d["traces"].append({"decision_id":"SIG-200M-LEGACY-001","state":"consumed","design_ref":"docs/CB6_DEVELOPMENT_EXECUTION_GATE.md","verification":["destructive fixture"]})
 p.write_text(json.dumps(d))
CASES.append(("superseded-consumed", mutate_superseded, "superseded decision consumed"))

def mutate_bad_spec(r):
 p=r/"v2/gates/current_spec.json"; d=json.loads(p.read_text()); d["signal"]["display"]["zoom_symbols"]["15"]="ghost"; p.write_text(json.dumps(d))
CASES.append(("invalid-current-spec", mutate_bad_spec, "symbol without dimensions"))

def mutate_retired(r):
 p=r/"docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md"; p.write_text(p.read_text().replace("RETIRED AS CANONICAL","CANONICAL AGAIN"))
CASES.append(("retired-design-reactivated", mutate_retired, "retired design lost retirement marker"))

def mutate_fake_implementation_enabled(r):
 p=r/"v2/gates/project_state.json"; d=json.loads(p.read_text())
 d["stage"]="IMPLEMENTATION_ENABLED"; d["feature_builds_allowed"]=True; d["design_verified"]=True
 d["canonical_design"]="docs/CB6_DEVELOPMENT_EXECUTION_GATE.md"; p.write_text(json.dumps(d))
 a=r/"v2/gates/authority_policy.json"; ad=json.loads(a.read_text()); ad["stage"]="IMPLEMENTATION_ENABLED"; a.write_text(json.dumps(ad))
 e=r/"v2/gates/evidence_inventory.json"; ed=json.loads(e.read_text()); ed["stage"]="IMPLEMENTATION_ENABLED"; e.write_text(json.dumps(ed))
CASES.append(("implementation-with-pending-decisions", mutate_fake_implementation_enabled, "implementation enabled with unconsumed active decisions"))

def mutate_historical_resource_inventory(r):
 p=r/"v2/audits/audit_signals.py"; s=p.read_text()
 s=s.replace("symbols = ['cb6-signal-'+s for s in sorted(set(spec['display']['zoom_symbols'].values()) | set(spec['display']['forward_zoom_symbols'].values()))]", "symbols = ['cb6-signal-'+s for s in spec['display']['symbols']]")
 p.write_text(s)
CASES.append(("historical-resource-inventory", mutate_historical_resource_inventory, "historical resource inventory"))

def mutate_missing_evidence(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 next(x for x in d["decisions"] if x["id"]=="PROC-001")["evidence"]=["docs/DOES_NOT_EXIST.md"]
 p.write_text(json.dumps(d))
CASES.append(("missing-evidence", mutate_missing_evidence, "evidence path missing"))

def mutate_duplicate_owner(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 x=next(x for x in d["decisions"] if x["id"]=="SIG-COVERAGE-001"); x["spec_key"]="signal.display.200m"
 p.write_text(json.dumps(d))
CASES.append(("duplicate-active-spec-owner", mutate_duplicate_owner, "multiple active owners for spec_key"))

def mutate_broken_supersession(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 next(x for x in d["decisions"] if x["id"]=="SIG-200M-LEGACY-001")["superseded_by"]="SIG-COVERAGE-001"
 p.write_text(json.dumps(d))
CASES.append(("broken-supersession", mutate_broken_supersession, "non-reciprocal supersession"))

def mutate_historical_authority(r):
 p=r/"docs/CB6_V2_MODULE_CONTRACTS.md"; p.write_text(p.read_text()+"\nStatus: CANONICAL IMPLEMENTATION BOUNDARIES\n")
CASES.append(("historical-authority-regained", mutate_historical_authority, "historical document regained authority"))

def mutate_stale_signal_authority(r):
 p=r/"docs/CB6_FROZEN_FEATURES.md"; p.write_text(p.read_text()+"\nThe Run #65 feature above remains the behavioral authority.\n")
CASES.append(("stale-signal-authority-regained", mutate_stale_signal_authority, "historical document regained authority"))

def mutate_evidence_missing_path(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"][0]["path"]="docs/DOES_NOT_EXIST_EVIDENCE.md"; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-missing-path", mutate_evidence_missing_path, "evidence inventory path missing"))

def mutate_evidence_bad_status(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"][0]["status"]="trusted-because-old"; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-bad-status", mutate_evidence_bad_status, "invalid evidence status"))

def mutate_evidence_duplicate_id(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"][1]["id"]=d["evidence"][0]["id"]; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-duplicate-id", mutate_evidence_duplicate_id, "evidence IDs missing/duplicated"))

for name,mutate,needle in CASES:
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo"
  shutil.copytree(SRC,root,ignore=shutil.ignore_patterns(".git","out","comaps"))
  mutate(root)
  cp=subprocess.run(["python3","v2/gates/verify_project_integrity.py"],cwd=root,text=True,capture_output=True)
  output=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in output:
   raise SystemExit(f"DESTRUCTIVE TEST FAIL {name}: rc={cp.returncode}\n{output}")
  print("PASS expected rejection:",name,"->",needle)
print("PASS all destructive integrity cases rejected")
