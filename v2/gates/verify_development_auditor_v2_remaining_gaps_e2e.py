#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/development_auditor_v2_remaining_gaps_e2e_cases.json").read_text())
a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
expected={"CF-01":"STOP","CF-02":"STOP","CF-03":"STOP","CF-04":"STOP","CF-05":"STOP"}
req=set(s["required"]);bind=set(a["approval"]["binding_fields"])
def decide(c):
 w=c["work_unit"]
 if not req.issubset(w) or not w.get("change_id") or not w.get("purpose") or not w.get("affected_domains") or not w.get("planned_paths"):return "STOP"
 for dim in w.get("dimensions",[]):
  if dim.get("applicability")=="BLOCKED":return "STOP"
  for ref in dim.get("evidence_refs",[]):
   if isinstance(ref,dict) and ref.get("work_unit_id")!=w["change_id"] and not ref.get("explicit_binding"):return "STOP"
 ap=w.get("approval",{})
 if not ap.get("bound"):return "STOP"
 if bind.issubset(ap):
  for k in bind:
   if ap.get(k)!=w.get(k):return "STOP"
 ir=w.get("independent_review",{})
 if not ir.get("accepted") or ir.get("evidence_type")=="implementation_success":return "STOP"
 return "PASS"
if d.get("sealed_acceptance_criteria")!=[
"CF-01 missing or mixed Work Unit identity must STOP",
"CF-02 cross-work-unit evidence reuse without explicit binding must STOP",
"CF-03 approval binding mismatch must STOP",
"CF-04 BLOCKED dimension cannot advance or PASS",
"CF-05 missing independent review or implementation-success substitution must STOP"]:e.append("SEALED AC")
if a.get("evidence_sufficiency",{}).get("cross_work_unit_evidence_reuse_without_explicit_binding_forbidden") is not True:e.append("cross-WU authority")
if a.get("independent_review",{}).get("implementation_success_claims_are_not_review_evidence") is not True:e.append("review substitution authority")
if s.get("pass_requires",{}).get("no_blocked_dimension") is not True:e.append("blocked authority")
cs={x["id"]:x for x in d.get("cases",[])}
if set(cs)!=set(expected):e.append("case set")
for cid,out in expected.items():
 if cs[cid].get("expected")!=out or decide(cs[cid])!=out:e.append(cid)
if e:
 print("AUDITOR V2 REMAINING GAPS E2E FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 REMAINING GAPS E2E PASS: 5 Work Unit-shaped gaps rejected")
