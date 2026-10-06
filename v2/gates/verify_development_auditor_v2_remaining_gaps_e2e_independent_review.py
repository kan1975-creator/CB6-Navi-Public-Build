#!/usr/bin/env python3
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/development_auditor_v2_remaining_gaps_e2e_cases.json").read_text())
a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
sealed=["CF-01 missing or mixed Work Unit identity must STOP","CF-02 cross-work-unit evidence reuse without explicit binding must STOP","CF-03 approval binding mismatch must STOP","CF-04 BLOCKED dimension cannot advance or PASS","CF-05 missing independent review or implementation-success substitution must STOP"]
if d.get("sealed_acceptance_criteria")!=sealed:e.append("SEALED AC mismatch")
if a.get("evidence_sufficiency",{}).get("cross_work_unit_evidence_reuse_without_explicit_binding_forbidden") is not True:e.append("cross-WU authority")
if a.get("independent_review",{}).get("implementation_success_claims_are_not_review_evidence") is not True:e.append("review substitution authority")
if a.get("independent_review",{}).get("required_before_pass") is not True:e.append("review-required authority")
if s.get("pass_requires",{}).get("no_blocked_dimension") is not True:e.append("blocked authority")
req=set(s.get("required",[]));bind=set(a.get("approval",{}).get("binding_fields",[]))
cs={x.get("id"):x for x in d.get("cases",[])}
if set(cs)!={"CF-01","CF-02","CF-03","CF-04","CF-05"}:e.append("case set")
for cid in ["CF-01","CF-02","CF-03","CF-04","CF-05"]:
 c=cs.get(cid,{});w=c.get("work_unit",{})
 if c.get("expected")!="STOP":e.append(cid+": expected")
 if not req.issubset(w):e.append(cid+": not Work Unit-shaped")
if cs.get("CF-01",{}).get("work_unit",{}).get("change_id"):e.append("CF-01 identity defect absent")
refs=cs.get("CF-02",{}).get("work_unit",{}).get("dimensions",[{}])[0].get("evidence_refs",[])
if not any(isinstance(x,dict) and x.get("work_unit_id")!="CF-02" and x.get("explicit_binding") is False for x in refs):e.append("CF-02 reuse defect absent")
w=cs.get("CF-03",{}).get("work_unit",{});ap=w.get("approval",{})
if not bind.issubset(ap) or all(ap.get(k)==w.get(k) for k in bind):e.append("CF-03 binding defect absent")
if not any(x.get("applicability")=="BLOCKED" for x in cs.get("CF-04",{}).get("work_unit",{}).get("dimensions",[])):e.append("CF-04 blocked defect absent")
ir=cs.get("CF-05",{}).get("work_unit",{}).get("independent_review",{})
if ir.get("accepted") is not False or ir.get("evidence_type")!="implementation_success":e.append("CF-05 review defect absent")
tree=ast.parse(Path(__file__).read_text());mod="verify_"+"development_auditor_v2_remaining_gaps_e2e";script=mod+".py"
for n in ast.walk(tree):
 if isinstance(n,ast.Import) and any(x.name==mod for x in n.names):e.append("candidate verifier import")
 if isinstance(n,ast.ImportFrom) and n.module==mod:e.append("candidate verifier from-import")
 if isinstance(n,ast.Constant) and n.value==script:e.append("candidate verifier execution")
if e:
 print("AUDITOR V2 REMAINING GAPS INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 REMAINING GAPS INDEPENDENT REVIEW PASS: 5 Work Unit-shaped cases independently reconstructed")
