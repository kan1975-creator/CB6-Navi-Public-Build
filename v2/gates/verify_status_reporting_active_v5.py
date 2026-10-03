#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v5.json").read_text(encoding="utf-8"))
if d.get("schema")!=5 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v5 identity/status invalid")
a=json.loads((R/"v2/gates/status_reporting_contract_v4.json").read_text(encoding="utf-8"))
if a.get("status")!="ACTIVE": e.append("historical ACTIVE v4 not preserved")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope"):
 if d.get(k)!=a.get(k): e.append("existing v4 contract changed: "+k)
for k in ("進めて推奨","スマホ操作が必要"):
 if d.get("rules",{}).get(k)!=a.get("rules",{}).get(k): e.append("existing v4 rule changed: "+k)
w=d.get("rules",{}).get("待ち",{}).get("wait_time_display",{})
if w.get("run_start_basis")!="IMMUTABLE_ORIGINAL_RUN_START": e.append("immutable run start missing")
if w.get("first_wait",{}).get("show_run_start_time_jst") is not True or w.get("first_wait",{}).get("next_check_basis")!="RECENT_ACTUAL_SAME_WORKFLOW_DURATION": e.append("first wait rule invalid")
l=w.get("later_wait",{})
for k in ("show_cumulative_elapsed_from_original_run_start","intermediate_check_must_not_reset_basis","next_check_is_remaining_interval","recalculate_from_original_start_and_recent_actual_duration"):
 if l.get(k) is not True: e.append("later wait rule invalid: "+k)
x=w.get("exceeded_normal_duration",{})
if x.get("use_shorter_reasonable_next_check_interval") is not True or x.get("restart_original_interval_forbidden") is not True: e.append("overdue wait rule invalid")
if w.get("completed_run",{}).get("report_completed_result_instead_of_wait") is not True: e.append("completed run rule invalid")
reg=json.loads((R/"v2/gates/operational_rule_registry_v8.json").read_text()); rules={x.get("id"):x for x in reg.get("rules",[])}; sr=rules.get("OPS-STATUS-REPORTING-001",{})
if reg.get("version")!=8 or sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v5.json": e.append("registry v8 active binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov.get("entries",[])}
if cov.get("registry")!="v2/gates/operational_rule_registry_v8.json" or ce.get("OPS-STATUS-REPORTING-001",{}).get("coverage_status")!="MACHINE_ENFORCED": e.append("machine coverage v8 missing")
ad=d.get("adoption",{})
if ad.get("candidate_validation_run_id")!=37125650903 or ad.get("independent_review_run_id")!=37125954991 or ad.get("independent_review_head")!="791db2b72556b877c35bfcebe752a8f3abdb1d27": e.append("v5 adoption evidence invalid")
if e:
 print("CB6 STATUS REPORTING V5 ACTIVE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V5 ACTIVE PASS: immutable wait timing + cumulative elapsed + remaining interval; registry v8+coverage+adoption enforced")
