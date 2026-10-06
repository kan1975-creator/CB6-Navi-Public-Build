#!/usr/bin/env python3
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/development_auditor_v2_stage_forgetting_e2e_cases.json").read_text())
a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
sealed=[
"SF-01 missing ACTIVE authority during RECONSTRUCT must STOP",
"SF-02 mandatory dimension falsely classified NOT_APPLICABLE must STOP",
"SF-03 missing counter-hypothesis for a material decision must CORRECT",
"SF-04 unresolved blocker omitted before PROPOSE must STOP",
"SF-05 missing validation evidence must FOLLOW-UP",
"SF-06 blocking independent-review disagreement must STOP",
"SF-07 exit audit with missing evidence must STOP"]
if d.get("sealed_acceptance_criteria")!=sealed:e.append("SEALED AC mismatch")
if a.get("revision")!=2 or len(a.get("acceptance_criteria",[]))!=18:e.append("Auditor V2 authority")
if a.get("semantic_audit",{}).get("requires_counter_hypothesis_or_alternative_for_material_decisions") is not True:e.append("counter-hypothesis authority")
if a.get("independent_review",{}).get("blocking_disagreement_forbids_pass") is not True:e.append("disagreement authority")
if a.get("exit_audit",{}).get("missing_evidence_forbids_pass") is not True:e.append("exit evidence authority")
if s.get("pass_requires",{}).get("mandatory_dimensions_applied") is not True:e.append("mandatory dimension authority")
if s.get("pass_requires",{}).get("no_unresolved_blocker") is not True:e.append("blocker authority")
if s.get("pass_requires",{}).get("validation_complete") is not True:e.append("validation authority")
expected={"SF-01":"STOP","SF-02":"STOP","SF-03":"CORRECT","SF-04":"STOP","SF-05":"FOLLOW-UP","SF-06":"STOP","SF-07":"STOP"}
cs={x.get("id"):x for x in d.get("cases",[])}
if set(cs)!=set(expected):e.append("case identity set")
for cid,out in expected.items():
 if cs.get(cid,{}).get("expected")!=out:e.append(cid+": declared expected differs from independently derived outcome")
if cs.get("SF-01",{}).get("active_authority_complete") is not False:e.append("SF-01 defect absent")
c2=cs.get("SF-02",{})
if c2.get("mandatory_dimensions_applied") is not False or c2.get("false_not_applicable")!="active_authority":e.append("SF-02 defect absent")
c3=cs.get("SF-03",{})
if c3.get("material_decision") is not True or c3.get("counter_hypothesis_complete") is not False:e.append("SF-03 defect absent")
c4=cs.get("SF-04",{})
if c4.get("unresolved_blocker") is not True or c4.get("blocker_omitted") is not True:e.append("SF-04 defect absent")
if cs.get("SF-05",{}).get("validation_evidence_complete") is not False:e.append("SF-05 defect absent")
if cs.get("SF-06",{}).get("blocking_disagreement") is not True:e.append("SF-06 defect absent")
if cs.get("SF-07",{}).get("exit_evidence_complete") is not False:e.append("SF-07 defect absent")
tree=ast.parse(Path(__file__).read_text())
candidate_module="verify_"+"development_auditor_v2_stage_forgetting_e2e"
candidate_script=candidate_module+".py"
for node in ast.walk(tree):
 if isinstance(node,ast.Import) and any(x.name==candidate_module for x in node.names):e.append("candidate verifier import dependency")
 if isinstance(node,ast.ImportFrom) and node.module==candidate_module:e.append("candidate verifier from-import dependency")
 if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value==candidate_script:e.append("candidate verifier execution reference")
if e:
 print("AUDITOR V2 STAGE FORGETTING E2E INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 STAGE FORGETTING E2E INDEPENDENT REVIEW PASS: 7 cases independently reconstructed from raw authority without candidate-verifier execution")
