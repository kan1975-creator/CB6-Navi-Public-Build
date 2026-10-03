#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v5.json").read_text(encoding="utf-8"))
if d.get("schema")!=5 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v5 identity/status invalid")
rev=d.get("revision",{})
if rev.get("from")!="v2/gates/status_reporting_contract_v4.json" or rev.get("supersedes")!="v2/gates/status_reporting_contract_v4.json" or not rev.get("reason"): e.append("v5 revision lineage invalid")
a=json.loads((R/"v2/gates/status_reporting_contract_v4.json").read_text(encoding="utf-8"))
if a.get("status")!="ACTIVE": e.append("ACTIVE v4 was not preserved")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope"):
 if d.get(k)!=a.get(k): e.append("existing v4 contract changed: "+k)
for k in ("進めて推奨","スマホ操作が必要"):
 if d.get("rules",{}).get(k)!=a.get("rules",{}).get(k): e.append("existing v4 rule changed: "+k)
w=d.get("rules",{}).get("待ち",{}).get("wait_time_display",{})
if w.get("run_start_basis")!="IMMUTABLE_ORIGINAL_RUN_START": e.append("immutable run start missing")
f=w.get("first_wait",{})
if f.get("show_run_start_time_jst") is not True or f.get("next_check_basis")!="RECENT_ACTUAL_SAME_WORKFLOW_DURATION": e.append("first wait rule invalid")
l=w.get("later_wait",{})
for k in ("show_cumulative_elapsed_from_original_run_start","intermediate_check_must_not_reset_basis","next_check_is_remaining_interval","recalculate_from_original_start_and_recent_actual_duration"):
 if l.get(k) is not True: e.append("later wait rule invalid: "+k)
x=w.get("exceeded_normal_duration",{})
if x.get("use_shorter_reasonable_next_check_interval") is not True or x.get("restart_original_interval_forbidden") is not True: e.append("overdue wait rule invalid")
if w.get("completed_run",{}).get("report_completed_result_instead_of_wait") is not True: e.append("completed run rule invalid")
h=w.get("history",{})
for k in ("same_workflow_recent_actual_duration_required_when_available","user_check_delay_must_not_distort_duration","calculation_detail_normally_hidden","show_detail_when_user_asks_basis"):
 if h.get(k) is not True: e.append("wait history rule invalid: "+k)
if d.get("activation",{}).get("direct_active_forbidden") is not True or d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V5 CANDIDATE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V5 CANDIDATE PASS: immutable wait timing + cumulative elapsed + remaining interval + overdue shortening + completed-result reporting; ACTIVE v4 preserved")
