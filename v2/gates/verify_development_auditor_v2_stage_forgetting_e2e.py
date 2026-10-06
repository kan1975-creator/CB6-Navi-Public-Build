#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
F=R/"v2/gates/development_auditor_v2_stage_forgetting_e2e_cases.json"
d=json.loads(F.read_text()); a=json.loads((R/d["auditor_contract"]).read_text()); s=json.loads((R/d["work_unit_schema"]).read_text())
errors=[]
sealed=[
"SF-01 missing ACTIVE authority during RECONSTRUCT must STOP",
"SF-02 mandatory dimension falsely classified NOT_APPLICABLE must STOP",
"SF-03 missing counter-hypothesis for a material decision must CORRECT",
"SF-04 unresolved blocker omitted before PROPOSE must STOP",
"SF-05 missing validation evidence must FOLLOW-UP",
"SF-06 blocking independent-review disagreement must STOP",
"SF-07 exit audit with missing evidence must STOP"]
if d.get("status")!="CANDIDATE" or d.get("sealed_acceptance_criteria")!=sealed: errors.append("SEALED AC changed")
if len(d.get("cases",[]))!=7 or {x.get("id") for x in d["cases"]}!={f"SF-{i:02d}" for i in range(1,8)}: errors.append("case set")
if a.get("revision")!=2 or len(a.get("acceptance_criteria",[]))!=18: errors.append("Auditor V2 authority")
if a.get("semantic_audit",{}).get("requires_counter_hypothesis_or_alternative_for_material_decisions") is not True: errors.append("counter-hypothesis authority")
if a.get("independent_review",{}).get("blocking_disagreement_forbids_pass") is not True: errors.append("disagreement authority")
if s.get("pass_requires",{}).get("no_unresolved_blocker") is not True or s.get("pass_requires",{}).get("validation_complete") is not True: errors.append("schema pass prerequisites")
def decide(c):
 if not c.get("active_authority_complete"): return "STOP"
 if not c.get("mandatory_dimensions_applied"): return "STOP"
 if c.get("unresolved_blocker"): return "STOP"
 if c.get("blocking_disagreement"): return "STOP"
 if not c.get("exit_evidence_complete"): return "STOP"
 if c.get("material_decision") and not c.get("counter_hypothesis_complete"): return "CORRECT"
 if not c.get("validation_evidence_complete"): return "FOLLOW-UP"
 return "PASS"
for c in d.get("cases",[]):
 got=decide(c)
 if got!=c.get("expected"): errors.append(f'{c.get("id")}: expected {c.get("expected")} got {got}')
if d["cases"][1].get("false_not_applicable")!="active_authority": errors.append("SF-02 applicability defect")
if d["cases"][3].get("blocker_omitted") is not True: errors.append("SF-04 omitted blocker")
required={"auditor_v2_core","existing_incident_e2e","registry_coverage","development_gate","method_freeze","signal","convenience","search","routing","renderer","apk","application_behavior"}
if set(d.get("non_interference",[]))!=required: errors.append("non-interference")
if errors:
 print("AUDITOR V2 STAGE FORGETTING E2E CANDIDATE FAIL:",*errors,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 STAGE FORGETTING E2E CANDIDATE PASS: 7 stage-specific forgetting defects rejected/corrected/followed-up")
