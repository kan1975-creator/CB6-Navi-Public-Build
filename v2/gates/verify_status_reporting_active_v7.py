#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v7.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v6.json").read_text(encoding="utf-8"))
if d.get("schema")!=7 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v7 identity/status invalid")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope","freshness_rule","fix_approval_boundary","report_tags","final_summary_display"):
 if d.get(k)!=a.get(k): e.append("existing ACTIVE v6 contract changed: "+k)
for k in ("進めて推奨","スマホ操作が必要"):
 if d["rules"].get(k)!=a["rules"].get(k): e.append("existing ACTIVE v6 rule changed: "+k)
dw=d["rules"]["待ち"]; aw=a["rules"]["待ち"]
for k in ("required_fields","parallel_read_only_work_allowed","post_wait_user_instruction"):
 if dw.get(k)!=aw.get(k): e.append("existing ACTIVE v6 wait rule changed: "+k)
for k in ("run_start_basis","first_wait","later_wait","completed_run","history"):
 if dw["wait_time_display"].get(k)!=aw["wait_time_display"].get(k): e.append("existing ACTIVE v6 wait timing changed: "+k)
x=dw["wait_time_display"].get("exceeded_normal_duration",{})
if x.get("basis")!="RECENT_SUCCESSFUL_SAME_WORKFLOW_ACTUAL_DURATIONS": e.append("normal duration evidence basis missing")
for k in ("recent_successful_same_workflow_actual_durations_required_when_available","fixed_or_unsubstantiated_threshold_forbidden","may_classify_exceeded_only_after_evidence_based_normal_duration_range_exceeded","use_shorter_reasonable_next_check_interval","restart_original_interval_forbidden"):
 if x.get(k) is not True: e.append("normal duration guard invalid: "+k)
reg=json.loads((R/"v2/gates/operational_rule_registry_v11.json").read_text()); sr={x.get("id"):x for x in reg["rules"]}.get("OPS-STATUS-REPORTING-001",{})
if reg.get("version")!=11 or sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v7.json": e.append("registry v11 active binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov["entries"]}
if cov.get("registry")!="v2/gates/operational_rule_registry_v11.json" or ce.get("OPS-STATUS-REPORTING-001",{}).get("coverage_status")!="MACHINE_ENFORCED": e.append("machine coverage v11 missing")
p=(R/"v2/governance/status_reporting_protocol.md").read_text(encoding="utf-8")
if "Status: ACTIVE (Status Reporting v7)" not in p: e.append("status reporting protocol is not ACTIVE v7")
for marker in ("approximate_wait_time", "next_check_timing", "parallel_work_available", "post_wait_user_instruction"):
 if marker not in p: e.append("status reporting protocol wait field missing: "+marker)
if "MACHINE_ENFORCED" not in p or "status_reporting_contract_v7.json" not in p: e.append("status reporting protocol authority binding missing")
ad=d.get("adoption",{})
if ad.get("candidate_validation_run_id")!=37128623188 or ad.get("independent_review_run_id")!=37128782100 or ad.get("independent_review_head")!="b016f9d10b549b3b0dd907c5cf32dffb1c073173": e.append("v7 adoption evidence invalid")
if e:
 print("CB6 STATUS REPORTING V7 ACTIVE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V7 ACTIVE PASS: evidence-based normal-duration guard + ACTIVE v6 behavior preserved; registry v11+coverage+adoption enforced")
