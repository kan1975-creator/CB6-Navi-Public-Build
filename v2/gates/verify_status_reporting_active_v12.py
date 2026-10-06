#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v12.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v11.json").read_text(encoding="utf-8"))
if d.get("schema")!=12 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE":e.append("ACTIVE v12 identity/status")
if a.get("schema")!=11 or a.get("status")!="ACTIVE":e.append("v11 basis not preserved")
if d.get("extends")!="v2/gates/status_reporting_contract_v11.json":e.append("v11 extension binding")
p=d.get("response_execution_preflight",{})
for k in ("required_before_every_cb6_progress_response","current_head_evidence_required","applicable_active_rules_evidence_required","classification_evidence_required","self_attestation_alone_forbidden","preflight_failure_forbids_normal_pass_response"):
 if p.get(k) is not True:e.append("preflight:"+k)
w=p.get("wait",{})
for k in ("run_identity_required_when_run_wait","first_wait_requires_original_start_time","later_wait_requires_cumulative_elapsed_from_original_start","next_check_timing_required","next_check_requires_measured_basis_or_duration_unknown","unsupported_time_estimate_forbidden","parallel_work_availability_required","post_wait_instruction_required"):
 if w.get(k) is not True:e.append("wait:"+k)
f=p.get("final_summary",{})
if f.get("four_lines_required") is not True or f.get("exact_order_required")!=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"] or f.get("must_be_response_end") is not True:e.append("final summary")
b=p.get("evidence_boundary",{})
if b.get("github_cannot_intercept_chatgpt_response_transmission") is not True or b.get("runtime_execution_remains_chatgpt_responsibility") is not True or b.get("machine_enforcement_must_not_be_overclaimed") is not True:e.append("runtime/machine boundary")
if d.get("activation",{}).get("candidate_validation_run_id")!=37408795958 or d.get("activation",{}).get("independent_review_run_id")!=37408997191:e.append("activation evidence")
if d.get("adoption",{}).get("status")!="ADOPTED":e.append("adoption")
ev=json.loads((R/"v2/gates/status_reporting_adoption_evidence_v12.json").read_text(encoding="utf-8"))
if ev.get("status")!="ACTIVE":e.append("adoption evidence status")
if e:
 print("CB6 STATUS REPORTING V12 ACTIVE FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("CB6 STATUS REPORTING V12 ACTIVE PASS: v11 basis preserved; per-response runtime preflight obligations are adopted and evidence-bound")
