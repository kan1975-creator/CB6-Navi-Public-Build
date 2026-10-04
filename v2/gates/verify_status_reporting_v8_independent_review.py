#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v8.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v7.json").read_text(encoding="utf-8"))
if d.get("schema")!=8 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v8 identity/status invalid")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope","freshness_rule","fix_approval_boundary","report_tags","final_summary_display"):
 if d.get(k)!=a.get(k): e.append("existing ACTIVE v7 contract changed: "+k)
for k in ("進めて推奨","スマホ操作が必要"):
 if d["rules"].get(k)!=a["rules"].get(k): e.append("existing ACTIVE v7 rule changed: "+k)
dw=d["rules"]["待ち"]; aw=a["rules"]["待ち"]
for k in ("required_fields","parallel_read_only_work_allowed","post_wait_user_instruction"):
 if dw.get(k)!=aw.get(k): e.append("existing ACTIVE v7 wait rule changed: "+k)
for k in ("run_start_basis","first_wait","later_wait","exceeded_normal_duration","completed_run","history"):
 if dw["wait_time_display"].get(k)!=aw["wait_time_display"].get(k): e.append("existing ACTIVE v7 wait timing changed: "+k)
x=dw["wait_time_display"].get("evidence_based_estimate",{})
for k in ("applies_to_all_waiting_processes","estimate_or_next_check_requires_evidence","fixed_or_unsubstantiated_estimate_forbidden"):
 if x.get(k) is not True: e.append("all-process wait evidence guard invalid: "+k)
req=x.get("required_evidence",[])
for k in ("current_run_or_step_start_time","current_elapsed_time","same_or_reasonably_comparable_historical_actual_duration_when_available"):
 if k not in req: e.append("required wait evidence missing: "+k)
if x.get("no_comparable_history_behavior")!="DISPLAY_DURATION_UNKNOWN" or x.get("duration_unknown_text")!="所要時間不明": e.append("unknown-duration fallback invalid")
if "all future CB6 waiting processes" not in x.get("applies_to",[]): e.append("future wait-process coverage missing")
q=x.get("reference_estimate_when_no_comparable_actual_history",{})
for k in ("allowed","must_be_labeled_as_reference_estimate","must_be_separate_from_official_next_check_guidance","basis_required","unsupported_guess_forbidden"):
 if q.get(k) is not True: e.append("reference estimate guard invalid: "+k)
if q.get("official_next_check_guidance_remains")!="所要時間不明": e.append("reference estimate replaced official unknown-duration guidance")
if q.get("display_condition")!="ONLY_WHEN_OFFICIAL_NEXT_CHECK_GUIDANCE_IS_DURATION_UNKNOWN": e.append("reference estimate display condition invalid")
for k in ("forbidden_when_official_guidance_is_evidence_based","display_required_when_duration_unknown_and_supported_basis_available","basis_detail_normally_hidden","show_basis_detail_when_user_asks"):
 if q.get(k) is not True: e.append("reference estimate conditional display guard invalid: "+k)
if len(q.get("allowed_basis",[]))<3: e.append("reference estimate concrete basis missing")
if q.get("normal_display_format")!="所要時間不明（参考推測：約○〜○分）": e.append("reference estimate normal display format invalid")
if d.get("activation",{}).get("direct_active_forbidden") is not True or d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V8 INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V8 INDEPENDENT REVIEW PASS: all waiting-process official guidance requires actual evidence; unknown history displays 所要時間不明; separately labeled concrete-evidence reference estimate allowed; ACTIVE v7 preserved")
