#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/development_auditor_candidate_v1.json").read_text(encoding="utf-8"))
if d.get("id")!="CB6-DEVELOPMENT-AUDITOR-V1" or d.get("status")!="CANDIDATE": e.append("auditor candidate identity/status invalid")
for k in ("latest_head_required_each_audit","active_authority_refetch_required_each_audit","chat_memory_is_not_authority","head_change_requires_resynchronization"):
 if d.get("freshness",{}).get(k) is not True: e.append("auditor freshness invalid: "+k)
if d.get("reuse",{}).get("existing_mechanisms_preferred") is not True: e.append("existing mechanism reuse not preferred")
for k in ("rules","specifications","lists_and_worklists","change_bound_approval","multidirectional_research","change_impact","implementation_and_validation_scope","atomic_and_traceability","evidence","known_failures_and_regressions"):
 if k not in d.get("audit_dimensions",[]): e.append("audit dimension missing: "+k)
a=d.get("approval_boundary",{})
if a.get("rule_id")!="OPS-USER-APPROVAL-BEFORE-FIX-001" or a.get("unknown_future_change_may_reuse_prior_approval") is not False or a.get("post_hoc_approval_forbidden") is not True: e.append("approval boundary invalid")
if set(d.get("outcomes",{}))!={"STOP","CORRECT","FOLLOW-UP","PASS"}: e.append("auditor outcomes invalid")
n=d.get("non_interference",{})
for k in ("application_source_change_forbidden","signal_behavior_change_forbidden","convenience_behavior_change_forbidden","search_routing_renderer_change_forbidden","existing_independent_review_weaken_forbidden","existing_gate_or_evidence_weaken_forbidden"):
 if n.get(k) is not True: e.append("non-interference invalid: "+k)
act=d.get("activation",{})
if act.get("self_activation_forbidden") is not True or act.get("direct_active_forbidden") is not True: e.append("activation boundary invalid")
if e:
 print("CB6 DEVELOPMENT AUDITOR V1 INDEPENDENT REVIEW FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 DEVELOPMENT AUDITOR V1 INDEPENDENT REVIEW PASS: freshness, reuse, audit coverage, approval boundary, outcomes and non-interference preserved")
