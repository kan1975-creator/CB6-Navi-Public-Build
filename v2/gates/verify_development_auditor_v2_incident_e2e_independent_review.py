#!/usr/bin/env python3
import ast
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
fixture=R/"v2/gates/development_auditor_v2_incident_e2e_cases.json"
d=json.loads(fixture.read_text())
a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
h=json.loads((R/"v2/gates/historical_incidents.json").read_text())
sealed=[
"E2E-01 implementation without prior bound approval must STOP",
"E2E-02 actual diff outside approved planned paths must STOP",
"E2E-03 Convenience implementation without fresh source-first research must STOP",
"E2E-04 incomplete impact coverage for a coupled JNI/UserMark change must CORRECT",
"E2E-05 applicable historical incident omitted from prior-failure comparison must CORRECT",
"E2E-06 negative conclusion based on a single zero-result search must STOP",
"E2E-07 evidence bound to a stale basis HEAD must STOP",
"E2E-08 a complete valid Work Unit must PASS"]
if d.get("sealed_acceptance_criteria")!=sealed:e.append("SEALED AC mismatch")
if a.get("revision")!=2 or len(a.get("acceptance_criteria",[]))!=18:e.append("Auditor V2 authority")
if a.get("approval",{}).get("post_hoc_approval_forbidden") is not True:e.append("approval authority")
if a.get("exit_audit",{}).get("actual_diff_must_match_declared_scope") is not True:e.append("diff authority")
if a.get("evidence_sufficiency",{}).get("negative_conclusion_from_single_zero_result_forbidden") is not True:e.append("zero-result authority")
if a.get("work_unit",{}).get("head_change_requires_resynchronization") is not True:e.append("HEAD freshness authority")
if s.get("pass_requires",{}).get("approval_bound_before_implementation") is not True:e.append("schema approval prerequisite")
if s.get("pass_requires",{}).get("actual_diff_within_approved_scope") is not True:e.append("schema diff prerequisite")
incident_ids={x.get("id") for x in h.get("incidents",[])}
expected={
"E2E-01":"STOP","E2E-02":"STOP","E2E-03":"STOP","E2E-04":"CORRECT",
"E2E-05":"CORRECT","E2E-06":"STOP","E2E-07":"STOP","E2E-08":"PASS"}
cs={x.get("id"):x for x in d.get("cases",[])}
if set(cs)!=set(expected):e.append("case identity set")
for cid,out in expected.items():
 c=cs.get(cid,{})
 if c.get("expected")!=out:e.append(cid+": declared expected differs from independently derived outcome")
# Independently prove the defect/validity represented by each fixture; do not execute/import candidate verifier.
if cs.get("E2E-01",{}).get("approval_bound_before_implementation") is not False:e.append("E2E-01 defect absent")
if cs.get("E2E-02",{}).get("actual_diff_within_approved_scope") is not False:e.append("E2E-02 defect absent")
c3=cs.get("E2E-03",{})
if c3.get("feature")!="convenience-brands" or c3.get("source_first_research_complete") is not False:e.append("E2E-03 source-first defect absent")
if c3.get("incident_id") not in incident_ids:e.append("E2E-03 incident not authoritative")
c4=cs.get("E2E-04",{})
if c4.get("impact_complete") is not False or set(c4.get("impact_domains",[]))!={"jni","usermark"}:e.append("E2E-04 impact defect absent")
c5=cs.get("E2E-05",{})
if c5.get("prior_failure_complete") is not False or c5.get("incident_id") not in incident_ids:e.append("E2E-05 prior-failure defect absent")
c6=cs.get("E2E-06",{})
if c6.get("negative_conclusion_sufficient") is not False or c6.get("negative_conclusion_basis")!="single_zero_result":e.append("E2E-06 evidence defect absent")
if cs.get("E2E-07",{}).get("head_current") is not False:e.append("E2E-07 stale-head defect absent")
valid=cs.get("E2E-08",{})
for k in ("approval_bound_before_implementation","actual_diff_within_approved_scope","source_first_research_complete","impact_complete","prior_failure_complete","negative_conclusion_sufficient","head_current","validation_complete","independent_review_accepted"):
 if valid.get(k) is not True:e.append("E2E-08 valid prerequisite missing:"+k)
tree=ast.parse(Path(__file__).read_text())
candidate_module="verify_"+"development_auditor_v2_incident_e2e"
candidate_script=candidate_module+".py"
for node in ast.walk(tree):
 if isinstance(node,ast.Import) and any(x.name==candidate_module for x in node.names):e.append("candidate verifier import dependency")
 if isinstance(node,ast.ImportFrom) and node.module==candidate_module:e.append("candidate verifier from-import dependency")
 if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value==candidate_script:e.append("candidate verifier execution reference")
if e:
 print("AUDITOR V2 INCIDENT E2E INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 INCIDENT E2E INDEPENDENT REVIEW PASS: 8 cases independently reconstructed from raw authority without candidate-verifier execution")
