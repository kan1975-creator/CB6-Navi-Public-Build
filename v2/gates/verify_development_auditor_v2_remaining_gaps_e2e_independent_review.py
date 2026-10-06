#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[];d=json.loads((R/"v2/gates/development_auditor_v2_remaining_gaps_e2e_cases.json").read_text());a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text());s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text());req=set(s["required"]);bind=set(a["approval"]["binding_fields"])
def bad(c):
 w=c["work_unit"];i=c["id"]
 if i=="CF-01A":return not w.get("change_id")
 if i=="CF-01B":return w.get("basis_head")!=w.get("target_head")
 if i=="CF-02":return any(isinstance(r,dict) and r.get("work_unit_id")!=w.get("change_id") and not r.get("explicit_binding") for x in w.get("dimensions",[]) for r in x.get("evidence_refs",[]))
 if i.startswith("CF-03"):return bind.issubset(w.get("approval",{})) and any(w["approval"].get(k)!=w.get(k) for k in bind)
 if i=="CF-04":return any(x.get("applicability")=="BLOCKED" for x in w.get("dimensions",[]))
 if i=="CF-05A":return not w.get("independent_review",{}).get("accepted")
 if i=="CF-05B":return w.get("independent_review",{}).get("evidence_type")=="implementation_success"
 return False
ids=["CF-01A","CF-01B","CF-02"]+[f"CF-03{x}" for x in "ABCDEF"]+["CF-04","CF-05A","CF-05B"];cs={x["id"]:x for x in d["cases"]}
if set(cs)!=set(ids):e.append("case set")
for i in ids:
 c=cs.get(i,{})
 if c.get("expected")!="STOP" or not req.issubset(c.get("work_unit",{})) or not bad(c):e.append(i)
if e:print("AUDITOR V2 REMAINING GAPS INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 REMAINING GAPS E2E PASS: 12 independent branches")
