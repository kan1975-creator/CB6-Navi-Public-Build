#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/development_auditor_v2_final_red_team_e2e_cases.json").read_text())
a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
m=json.loads((R/"v2/gates/development_method_contract.json").read_text())
sealed=["RT-01 risk self-declaration cannot reduce mandatory audit depth and must STOP","RT-02 conditional NOT_APPLICABLE without reason and applicability evidence must STOP","RT-03 HEAD change during a Work Unit without resynchronization must STOP","RT-04 applicable Development Method pipeline obligation omitted before implementation must STOP","RT-05 blocking defect cannot be downgraded to a weaker failure outcome and must STOP"]
if d.get("sealed_acceptance_criteria")!=sealed:e.append("SEALED AC")
if a.get("risk",{}).get("self_declared_low_cannot_reduce_mandatory_checks") is not True:e.append("risk authority")
if a.get("applicability",{}).get("conditional_not_applicable_requires_reason_and_evidence") is not True:e.append("N/A authority")
if a.get("work_unit",{}).get("head_change_requires_resynchronization") is not True:e.append("resync authority")
req=set(s.get("required",[]));pipe=m.get("feature_development_pipeline",[])
cs={x["id"]:x for x in d.get("cases",[])}
if set(cs)!={"RT-01","RT-02","RT-03","RT-04","RT-05"}:e.append("case set")
for cid,c in cs.items():
 w=c.get("work_unit",{})
 if c.get("expected")!="STOP" or not req.issubset(w):e.append(cid+": shape/expected")
r=cs["RT-01"]["work_unit"].get("risk",{})
if r.get("declared")!="low" or r.get("mandatory_checks_reduced") is not True:e.append("RT-01 defect")
dims=cs["RT-02"]["work_unit"].get("dimensions",[])
if not any(x.get("applicability")=="NOT_APPLICABLE" and (not x.get("reason") or not x.get("applicability_evidence_refs")) for x in dims):e.append("RT-02 defect")
rs=cs["RT-03"]["work_unit"].get("resynchronization",{})
if rs.get("head_changed") is not True or rs.get("resynchronized") is not False:e.append("RT-03 defect")
mp=cs["RT-04"]["work_unit"].get("method_pipeline",{});app=mp.get("applicable",[]);done=mp.get("completed",[])
if app!=pipe or not mp.get("implementation_started") or "change_impact_before_implementation" in done or "change_impact_before_implementation" not in app:e.append("RT-04 defect/method authority")
w=cs["RT-05"]["work_unit"]
if w.get("blocking_defect") is not True or w.get("outcome")!="FOLLOW-UP":e.append("RT-05 defect")
if e:
 print("AUDITOR V2 FINAL RED TEAM E2E FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 FINAL RED TEAM E2E PASS: 5 authority-backed bypasses rejected")
