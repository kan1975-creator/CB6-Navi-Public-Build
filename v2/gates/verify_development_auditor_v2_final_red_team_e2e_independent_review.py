#!/usr/bin/env python3
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/development_auditor_v2_final_red_team_e2e_cases.json").read_text())
a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
m=json.loads((R/"v2/gates/development_method_contract.json").read_text())
sealed=["RT-01 risk self-declaration cannot reduce mandatory audit depth and must STOP","RT-02 conditional NOT_APPLICABLE without reason and applicability evidence must STOP","RT-03 HEAD change during a Work Unit without resynchronization must STOP","RT-04 applicable Development Method pipeline obligation omitted before implementation must STOP","RT-05 blocking defect cannot be downgraded to a weaker failure outcome and must STOP"]
if d.get("sealed_acceptance_criteria")!=sealed:e.append("SEALED AC mismatch")
if a.get("risk",{}).get("self_declared_low_cannot_reduce_mandatory_checks") is not True:e.append("RT-01 authority")
if a.get("applicability",{}).get("conditional_not_applicable_requires_reason_and_evidence") is not True:e.append("RT-02 authority")
if a.get("work_unit",{}).get("head_change_requires_resynchronization") is not True:e.append("RT-03 authority")
req=set(s.get("required",[]));pipe=m.get("feature_development_pipeline",[])
cs={x.get("id"):x for x in d.get("cases",[])}
if set(cs)!={"RT-01","RT-02","RT-03","RT-04","RT-05"}:e.append("case set")
for cid in ["RT-01","RT-02","RT-03","RT-04","RT-05"]:
 c=cs.get(cid,{});w=c.get("work_unit",{})
 if c.get("expected")!="STOP" or not req.issubset(w):e.append(cid+": shape/expected")
r=cs["RT-01"]["work_unit"].get("risk",{})
if not(r.get("declared")=="low" and r.get("mandatory_checks_reduced") is True):e.append("RT-01 defect absent")
ds=cs["RT-02"]["work_unit"].get("dimensions",[])
if not any(x.get("applicability")=="NOT_APPLICABLE" and (not x.get("reason") or not x.get("applicability_evidence_refs")) for x in ds):e.append("RT-02 defect absent")
rs=cs["RT-03"]["work_unit"].get("resynchronization",{})
if not(rs.get("head_changed") is True and rs.get("resynchronized") is False):e.append("RT-03 defect absent")
mp=cs["RT-04"]["work_unit"].get("method_pipeline",{})
if mp.get("applicable")!=pipe or not mp.get("implementation_started") or "change_impact_before_implementation" in mp.get("completed",[]):e.append("RT-04 defect absent")
w=cs["RT-05"]["work_unit"]
if not(w.get("blocking_defect") is True and w.get("outcome")=="FOLLOW-UP"):e.append("RT-05 defect absent")
tree=ast.parse(Path(__file__).read_text());mod="verify_"+"development_auditor_v2_final_red_team_e2e";script=mod+".py"
for n in ast.walk(tree):
 if isinstance(n,ast.Import) and any(x.name==mod for x in n.names):e.append("candidate import")
 if isinstance(n,ast.ImportFrom) and n.module==mod:e.append("candidate from-import")
 if isinstance(n,ast.Constant) and n.value==script:e.append("candidate execution")
if e:
 print("AUDITOR V2 FINAL RED TEAM INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 FINAL RED TEAM INDEPENDENT REVIEW PASS: 5 cases independently reconstructed")
