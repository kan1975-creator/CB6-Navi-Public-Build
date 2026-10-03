#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v7.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v6.json").read_text(encoding="utf-8"))
if d.get("schema")!=7 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v7 identity/status invalid")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope","freshness_rule","fix_approval_boundary","report_tags","final_summary_display"):
 if d.get(k)!=a.get(k): e.append("existing v6 contract changed: "+k)
for k in ("進めて推奨","スマホ操作が必要"):
 if d.get("rules",{}).get(k)!=a.get("rules",{}).get(k): e.append("existing v6 rule changed: "+k)
dw=d["rules"]["待ち"]; aw=a["rules"]["待ち"]
for k in ("required_fields","parallel_read_only_work_allowed","post_wait_user_instruction"):
 if dw.get(k)!=aw.get(k): e.append("existing v6 wait rule changed: "+k)
for k in ("run_start_basis","first_wait","later_wait","completed_run","history"):
 if dw["wait_time_display"].get(k)!=aw["wait_time_display"].get(k): e.append("existing v6 wait timing changed: "+k)
x=dw["wait_time_display"].get("exceeded_normal_duration",{})
if x.get("basis")!="RECENT_SUCCESSFUL_SAME_WORKFLOW_ACTUAL_DURATIONS": e.append("normal duration evidence basis missing")
for k in ("recent_successful_same_workflow_actual_durations_required_when_available","fixed_or_unsubstantiated_threshold_forbidden","may_classify_exceeded_only_after_evidence_based_normal_duration_range_exceeded","use_shorter_reasonable_next_check_interval","restart_original_interval_forbidden"):
 if x.get(k) is not True: e.append("normal duration guard invalid: "+k)
if d.get("activation",{}).get("direct_active_forbidden") is not True or d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V7 CANDIDATE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V7 CANDIDATE PASS: evidence-based normal-duration overrun only; other ACTIVE v6 rules preserved")
