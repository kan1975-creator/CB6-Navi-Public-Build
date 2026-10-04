#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v9.json").read_text(encoding="utf-8")); a=json.loads((R/"v2/gates/status_reporting_contract_v8.json").read_text(encoding="utf-8"))
if d.get("schema")!=9 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v9 identity/status invalid")
for k in a:
 if k not in ("schema","status","source","revision","adoption","activation") and d.get(k)!=a.get(k): e.append("existing ACTIVE v8 contract changed: "+k)
p=d.get("response_preflight",{})
for k in ("required_before_every_cb6_progress_response","github_current_authority_check_required","applicable_active_rules_must_be_selected","response_must_be_checked_against_selected_active_rules","contradiction_must_fail_closed","normal_hidden_detail_policy_must_be_enforced","final_summary_format_must_be_checked","chat_memory_alone_forbidden"):
 if p.get(k) is not True: e.append("response preflight guard invalid: "+k)
if p.get("preflight_result_required")!="PASS_BEFORE_RESPONSE" or p.get("scope")!="all_CB6_progress_status_responses": e.append("response preflight scope/result invalid")
m=p.get("enforcement_model",{})
for k in ("github_does_not_guarantee_response_transmission_interception","machine_enforced_claim_limited_to_repository_contract_and_verification","runtime_execution_is_operational_responsibility"):
 if m.get(k) is not True: e.append("response preflight enforcement boundary invalid: "+k)
for k in ("contract_fields_and_scope","candidate_and_active_verifier_behavior","destructive_fail_closed_cases","registry_and_coverage_linkage"):
 if k not in m.get("github_machine_verifiable",[]): e.append("github-verifiable boundary missing: "+k)
for k in ("perform_preflight_before_each_CB6_progress_response","use_current_GitHub_authority","select_applicable_ACTIVE_rules","check_response_against_selected_rules","withhold_or_correct_response_when_preflight_does_not_pass"):
 if k not in m.get("chatgpt_runtime_responsibility",[]): e.append("runtime responsibility missing: "+k)
if d.get("adoption",{}).get("candidate_validation_run_id")!=37170357405 or d.get("adoption",{}).get("independent_review_run_id")!=37170358868: e.append("v9 adoption evidence invalid")
if d.get("activation",{}).get("status")!="ACTIVE": e.append("v9 activation lifecycle not finalized")
if d.get("adoption",{}).get("status")!="ADOPTED": e.append("v9 adoption lifecycle not finalized")
ev=json.loads((R/"v2/gates/status_reporting_adoption_evidence_v9.json").read_text(encoding="utf-8"))
if ev.get("status")!="ACTIVE" or ev.get("next_required")!=[]: e.append("v9 adoption evidence still pending")
if e:
 print("CB6 STATUS REPORTING V9 ACTIVE FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 STATUS REPORTING V9 ACTIVE PASS: ACTIVE v8 preserved; repository verification and ChatGPT runtime responsibility explicitly separated")
