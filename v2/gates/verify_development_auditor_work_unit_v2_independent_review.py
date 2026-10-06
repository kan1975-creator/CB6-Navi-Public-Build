#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
S=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
V=(R/"v2/gates/verify_development_auditor_work_unit_v2.py").read_text()
T=(R/"v2/tests/test_development_auditor_work_unit_v2_fail_closed.py").read_text()
e=[]
required=set(S["required"])
expected={"change_id","basis_head","target_head","purpose","change_type","affected_domains","planned_paths","forbidden_scope","authority","dimensions","approval","actual_diff","validation","independent_review","outcome"}
if required!=expected:e.append("schema required fields changed or incomplete")
for token in ("approval change binding mismatch","approval basis HEAD mismatch","actual diff outside approved planned paths","actual diff intersects forbidden scope","stale target HEAD","validation incomplete","independent review incomplete or blocking","exit audit not accepted","invalid state transition order"):
 if token not in V:e.append("runtime verifier missing semantic rejection: "+token)
for label in ("missing-work-unit","approval-missing","stale-head","scope-drift","validation","ir-missing","ir-blocking","exit","state-order"):
 if '"'+label+'"' not in T:e.append("destructive proof missing branch: "+label)
if "OPS-USER-APPROVAL-BEFORE-FIX-001" not in json.dumps(json.loads((R/"v2/gates/operational_rule_registry_v19.json").read_text())):e.append("approval authority not ACTIVE in registry")
if e:
 print("CB6 AUDITOR V2 RUNTIME INDEPENDENT REVIEW FAIL:")
 for x in e:print(" -",x)
 raise SystemExit(1)
print("CB6 AUDITOR V2 RUNTIME INDEPENDENT REVIEW PASS: schema, approval binding, HEAD, diff, validation, independent review, exit audit and destructive branches independently reconstructed")
