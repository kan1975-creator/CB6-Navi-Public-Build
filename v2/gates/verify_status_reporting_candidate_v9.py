#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v9.json").read_text(encoding="utf-8")); a=json.loads((R/"v2/gates/status_reporting_contract_v8.json").read_text(encoding="utf-8"))
if d.get("schema")!=9 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v9 identity/status invalid")
for k in a:
 if k not in ("schema","status","source","revision","adoption") and d.get(k)!=a.get(k): e.append("existing ACTIVE v8 contract changed: "+k)
p=d.get("response_preflight",{})
for k in ("required_before_every_cb6_progress_response","github_current_authority_check_required","applicable_active_rules_must_be_selected","response_must_be_checked_against_selected_active_rules","contradiction_must_fail_closed","normal_hidden_detail_policy_must_be_enforced","final_summary_format_must_be_checked","chat_memory_alone_forbidden"):
 if p.get(k) is not True: e.append("response preflight guard invalid: "+k)
if p.get("preflight_result_required")!="PASS_BEFORE_RESPONSE" or p.get("scope")!="all_CB6_progress_status_responses": e.append("response preflight scope/result invalid")
if d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V9 CANDIDATE FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 STATUS REPORTING V9 CANDIDATE PASS: ACTIVE v8 preserved; fail-closed response preflight required")
