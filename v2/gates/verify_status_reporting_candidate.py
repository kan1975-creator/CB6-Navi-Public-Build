#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
P=R/"v2/gates/status_reporting_contract_candidate_v1.json"
d=json.loads(P.read_text(encoding="utf-8")); e=[]
if d.get("schema")!=1 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate identity/status invalid")
expected=["進めて推奨","待ち","スマホ操作が必要"]
if d.get("allowed_classifications")!=expected: e.append("classification set/order drifted")
if d.get("exactly_one_classification_required") is not True: e.append("exactly-one classification not required")
r=d.get("rules",{})
if set(r)!=set(expected): e.append("classification rule keys mismatch")
if r.get("進めて推奨",{}).get("chat_instruction_wait_alone_forbidden") is not True: e.append("chat instruction wait allowed")
if r.get("待ち",{}).get("required_fields")!=["approximate_wait_time","next_check_timing","parallel_work_available"]: e.append("wait fields invalid")
if r.get("待ち",{}).get("parallel_read_only_work_allowed") is not True: e.append("parallel read-only work disabled")
if r.get("スマホ操作が必要",{}).get("required_fields")!=["required_device_action","required_evidence"]: e.append("device fields invalid")
f=d.get("freshness_rule",{})
for k in ("progress_query_requires_current_head","progress_query_requires_relevant_run","material_log_evidence_requires_fresh_raw_log"):
 if f.get(k) is not True: e.append("freshness weakened: "+k)
if f.get("delegates_stale_state_authority_to")!="v2/gates/notification_stale_state.json": e.append("stale-state delegation invalid")
if not (R/f.get("delegates_stale_state_authority_to","")).is_file(): e.append("stale-state authority missing")
a=d.get("fix_approval_boundary",{})
if a.get("delegates_to")!="OPS-USER-APPROVAL-BEFORE-FIX-001" or a.get("generic_progress_permission_is_not_specific_fix_approval") is not True: e.append("fix approval boundary invalid")
reg=json.loads((R/"v2/gates/operational_rule_registry_v3.json").read_text(encoding="utf-8"))
ids={x.get("id"):x for x in reg.get("rules",[])}
if a.get("delegates_to") not in ids or ids[a["delegates_to"]].get("status")!="ACTIVE": e.append("approval delegation target not ACTIVE")
ac=d.get("activation",{})
if ac.get("direct_active_forbidden") is not True: e.append("direct activation allowed")
req={"positive_verification","destructive_test","successful_github_run_evidence","independent_review","explicit_user_adoption","machine_enforced_coverage"}
if set(ac.get("requires",[]))!=req: e.append("activation requirements invalid")
if e:
 print("CB6 STATUS REPORTING CANDIDATE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING CANDIDATE PASS: classes=3; stale-state=delegated; fix-approval=delegated; direct-active=forbidden")
