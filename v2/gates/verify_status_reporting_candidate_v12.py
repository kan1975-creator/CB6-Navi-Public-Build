#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
c=json.loads((R/"v2/gates/status_reporting_contract_candidate_v12.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v11.json").read_text(encoding="utf-8"))
if c.get("schema")!=12 or c.get("status")!="CANDIDATE" or c.get("extends")!="v2/gates/status_reporting_contract_v11.json": e.append("candidate identity")
if a.get("schema")!=11 or a.get("status")!="ACTIVE": e.append("ACTIVE v11 authority")
p=c.get("response_execution_preflight",{})
for k in ("required_before_every_cb6_progress_response","current_head_evidence_required","applicable_active_rules_evidence_required","classification_evidence_required","self_attestation_alone_forbidden","preflight_failure_forbids_normal_pass_response"):
 if p.get(k) is not True:e.append("preflight "+k)
w=p.get("wait",{})
for k in ("run_identity_required_when_run_wait","first_wait_requires_original_start_time","later_wait_requires_cumulative_elapsed_from_original_start","next_check_timing_required","next_check_requires_measured_basis_or_duration_unknown","unsupported_time_estimate_forbidden","parallel_work_availability_required","post_wait_instruction_required"):
 if w.get(k) is not True:e.append("wait "+k)
f=p.get("final_summary",{})
if f.get("four_lines_required") is not True or f.get("exact_order_required")!=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"] or f.get("must_be_response_end") is not True:e.append("final summary")
b=p.get("evidence_boundary",{})
for k in ("github_can_verify_contract_and_destructive_cases","github_cannot_intercept_chatgpt_response_transmission","runtime_execution_remains_chatgpt_responsibility","machine_enforcement_must_not_be_overclaimed"):
 if b.get(k) is not True:e.append("evidence boundary "+k)
n=c.get("non_interference",{})
for k in ("active_v11_change_forbidden","registry_coverage_change_forbidden","method_freeze_change_forbidden","development_gate_change_forbidden","auditor_v2_change_forbidden","application_behavior_change_forbidden"):
 if n.get(k) is not True:e.append("non-interference "+k)
if e:
 print("CB6 STATUS REPORTING V12 CANDIDATE FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("CB6 STATUS REPORTING V12 CANDIDATE PASS: per-response execution preflight is fail-closed and ACTIVE v11 remains authority")
