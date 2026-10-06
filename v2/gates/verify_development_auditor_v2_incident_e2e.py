#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
F=R/"v2/gates/development_auditor_v2_incident_e2e_cases.json"
d=json.loads(F.read_text()); a=json.loads((R/d["auditor_contract"]).read_text()); s=json.loads((R/d["work_unit_schema"]).read_text()); h=json.loads((R/d["historical_incident_authority"]).read_text())
errors=[]
sealed=[
"E2E-01 implementation without prior bound approval must STOP",
"E2E-02 actual diff outside approved planned paths must STOP",
"E2E-03 Convenience implementation without fresh source-first research must STOP",
"E2E-04 incomplete impact coverage for a coupled JNI/UserMark change must CORRECT",
"E2E-05 applicable historical incident omitted from prior-failure comparison must CORRECT",
"E2E-06 negative conclusion based on a single zero-result search must STOP",
"E2E-07 evidence bound to a stale basis HEAD must STOP",
"E2E-08 a complete valid Work Unit must PASS"]
if d.get("status")!="CANDIDATE" or d.get("sealed_acceptance_criteria")!=sealed: errors.append("SEALED AC changed")
if len(d.get("cases",[]))!=8 or {x.get("id") for x in d["cases"]}!={f"E2E-{i:02d}" for i in range(1,9)}: errors.append("case set")
if a.get("revision")!=2 or len(a.get("acceptance_criteria",[]))!=18: errors.append("Auditor V2 authority")
if s.get("negative_conclusion",{}).get("single_zero_result_insufficient") is not True: errors.append("zero-result authority")
incident_ids={x["id"] for x in h.get("incidents",[])}
def decide(c):
 if not c.get("head_current"): return "STOP"
 if not c.get("approval_bound_before_implementation"): return "STOP"
 if not c.get("actual_diff_within_approved_scope"): return "STOP"
 if not c.get("source_first_research_complete"): return "STOP"
 if not c.get("negative_conclusion_sufficient"): return "STOP"
 if not c.get("impact_complete"): return "CORRECT"
 if not c.get("prior_failure_complete"): return "CORRECT"
 if not c.get("validation_complete") or not c.get("independent_review_accepted"): return "FOLLOW-UP"
 return "PASS"
for c in d.get("cases",[]):
 if c.get("incident_id") and c["incident_id"] not in incident_ids: errors.append(c["id"]+": unknown incident")
 got=decide(c)
 if got!=c.get("expected"): errors.append(f'{c.get("id")}: expected {c.get("expected")} got {got}')
if d["cases"][2].get("feature")!="convenience-brands": errors.append("E2E-03 feature")
if d["cases"][5].get("negative_conclusion_basis")!="single_zero_result": errors.append("E2E-06 basis")
if set(d["cases"][3].get("impact_domains",[]))!={"jni","usermark"}: errors.append("E2E-04 coupled impact")
required={"auditor_v2_core","registry_coverage","development_gate","method_freeze","existing_independent_review","signal","convenience","search","routing","renderer","apk","application_behavior"}
if set(d.get("non_interference",[]))!=required: errors.append("non-interference")
if errors:
 print("AUDITOR V2 INCIDENT E2E CANDIDATE FAIL:",*errors,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 INCIDENT E2E CANDIDATE PASS: 7 invalid incident-shaped Work Units rejected/corrected and complete Work Unit passed")
