#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/development_auditor_candidate_v1.json").read_text(encoding="utf-8"))
if d.get("id")!="CB6-DEVELOPMENT-AUDITOR-V1": e.append("auditor identity invalid")
for k in ("latest_head_required_each_audit","active_authority_refetch_required_each_audit","chat_memory_is_not_authority","head_change_requires_resynchronization"):
 if d.get("freshness",{}).get(k) is not True: e.append("auditor freshness invalid: "+k)
if set(d.get("outcomes",{}))!={"STOP","CORRECT","FOLLOW-UP","PASS"}: e.append("auditor outcomes invalid")
a=d.get("approval_boundary",{})
if a.get("rule_id")!="OPS-USER-APPROVAL-BEFORE-FIX-001" or a.get("unknown_future_change_may_reuse_prior_approval") is not False or a.get("post_hoc_approval_forbidden") is not True: e.append("approval boundary invalid")
n=d.get("non_interference",{})
for k in ("application_source_change_forbidden","signal_behavior_change_forbidden","convenience_behavior_change_forbidden","search_routing_renderer_change_forbidden","existing_independent_review_weaken_forbidden","existing_gate_or_evidence_weaken_forbidden"):
 if n.get(k) is not True: e.append("non-interference invalid: "+k)
ev=json.loads((R/"v2/gates/development_auditor_adoption_evidence_v1.json").read_text(encoding="utf-8"))
if ev.get("status")!="ACTIVE" or ev.get("next_required")!=[]: e.append("auditor adoption evidence invalid")
reg=json.loads((R/"v2/gates/operational_rule_registry_v17.json").read_text(encoding="utf-8")); cov=json.loads((R/"v2/gates/rule_coverage.json").read_text(encoding="utf-8"))
rr=[x for x in reg.get("rules",[]) if x.get("id")=="CB6-DEVELOPMENT-AUDITOR-V1"]
if len(rr)!=1 or rr[0].get("status")!="ACTIVE": e.append("auditor registry activation invalid")
if not any(x.get("rule_id")=="CB6-DEVELOPMENT-AUDITOR-V1" and x.get("coverage_status")=="MACHINE_ENFORCED" for x in cov.get("entries",[])): e.append("auditor machine coverage missing")
if e:
 print("CB6 DEVELOPMENT AUDITOR V1 ACTIVE FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 DEVELOPMENT AUDITOR V1 ACTIVE PASS: freshness, approval boundary, outcomes, non-interference and machine coverage preserved")
