#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
c=json.loads((R/"v2/gates/status_reporting_contract_candidate_v5.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v4.json").read_text(encoding="utf-8"))
if c.get("schema")!=5 or c.get("rule_id")!="OPS-STATUS-REPORTING-001" or c.get("status")!="CANDIDATE": e.append("v5 candidate identity/status invalid")
w=c.get("rules",{}).get("待ち",{}).get("wait_time_display",{})
if w.get("run_start_basis")!="IMMUTABLE_ORIGINAL_RUN_START": e.append("immutable run start missing")
f=w.get("first_wait",{})
if f.get("show_run_start_time_jst") is not True or f.get("next_check_basis")!="RECENT_ACTUAL_SAME_WORKFLOW_DURATION": e.append("first wait rule invalid")
l=w.get("later_wait",{})
for k in ("show_cumulative_elapsed_from_original_run_start","intermediate_check_must_not_reset_basis","next_check_is_remaining_interval","recalculate_from_original_start_and_recent_actual_duration"):
 if l.get(k) is not True: e.append("later wait rule invalid: "+k)
x=w.get("exceeded_normal_duration",{})
if x.get("use_shorter_reasonable_next_check_interval") is not True or x.get("restart_original_interval_forbidden") is not True: e.append("overdue wait rule invalid")
if w.get("completed_run",{}).get("report_completed_result_instead_of_wait") is not True: e.append("completed run rule invalid")
if a.get("schema")!=4 or a.get("status")!="ACTIVE": e.append("ACTIVE v4 authority changed")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope"):
 if c.get(k)!=a.get(k): e.append("existing ACTIVE v4 contract changed in candidate: "+k)
for k in ("進めて推奨","スマホ操作が必要"):
 if c.get("rules",{}).get(k)!=a.get("rules",{}).get(k): e.append("existing ACTIVE v4 rule changed in candidate: "+k)
if c.get("activation",{}).get("direct_active_forbidden") is not True or c.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("v5 candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V5 INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V5 INDEPENDENT REVIEW PASS: wait timing candidate verified; ACTIVE v4 preserved; self-activation blocked")
