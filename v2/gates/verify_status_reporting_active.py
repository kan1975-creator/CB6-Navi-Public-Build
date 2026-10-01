#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];d=json.loads((R/"v2/gates/status_reporting_contract_v1.json").read_text(encoding="utf-8"));e=[]
if d.get("schema")!=1 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE":e.append("active identity/status invalid")
s=d.get("scope",{});wl=R/s.get("consolidated_worklist","")
if s.get("type")!="CB6_PROJECT_WIDE_CROSS_CUTTING":e.append("scope not project-wide")
for k in ("all_33_items_mandatory","applies_to_all_derivative_work","applies_to_all_future_work","applies_to_unknown_future_features_without_enumeration"):
 if s.get(k) is not True:e.append("scope weakened: "+k)
if s.get("consolidated_worklist_required_item_count")!=33:e.append("33-item requirement missing")
if not wl.is_file():e.append("worklist missing")
else:
 nums={int(x) for x in re.findall(r'^(\d+)\.\s+',wl.read_text(encoding="utf-8"),re.M)}
 if set(range(1,34))-nums:e.append("worklist missing item(s) 1..33")
if s.get("feature_specific_override_may_weaken_or_disable") is not False or s.get("new_feature_requires_explicit_opt_in") is not False:e.append("scope override/opt-in invalid")
tags=d.get("report_tags",{})
if tags.get("required_at_report_start") is not True or tags.get("allowed")!=["ガバナンス","信号機","コンビニ","その他"] or tags.get("governance_report_requires")!="ガバナンス":e.append("report tags invalid")
if tags.get("multiple_tags_allowed_for_cross_domain_report") is not True or tags.get("tag_presence_does_not_replace_status_classification") is not True:e.append("report tag semantics invalid")
expected=["進めて推奨","待ち","スマホ操作が必要"]
if d.get("allowed_classifications")!=expected or d.get("exactly_one_classification_required") is not True:e.append("classification invalid")
r=d.get("rules",{})
if r.get("進めて推奨",{}).get("chat_instruction_wait_alone_forbidden") is not True:e.append("chat wait allowed")
if r.get("待ち",{}).get("required_fields")!=["approximate_wait_time","next_check_timing","parallel_work_available"] or r.get("待ち",{}).get("parallel_read_only_work_allowed") is not True:e.append("wait invalid")
if r.get("スマホ操作が必要",{}).get("required_fields")!=["required_device_action","required_evidence"]:e.append("device invalid")
f=d.get("freshness_rule",{})
for k in ("progress_query_requires_current_head","progress_query_requires_relevant_run","material_log_evidence_requires_fresh_raw_log"):
 if f.get(k) is not True:e.append("freshness weakened: "+k)
a=d.get("fix_approval_boundary",{})
if a.get("delegates_to")!="OPS-USER-APPROVAL-BEFORE-FIX-001":e.append("approval delegation invalid")
for k in ("investigation_permission_is_not_fix_permission","generic_progress_permission_is_not_specific_fix_approval","old_approval_reuse_for_different_change_forbidden"):
 if a.get(k) is not True:e.append("approval boundary weakened: "+k)
reg=json.loads((R/"v2/gates/operational_rule_registry_v3.json").read_text()); rules={x.get("id"):x for x in reg.get("rules",[])}
sr=rules.get("OPS-STATUS-REPORTING-001",{})
if sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v1.json":e.append("registry active binding invalid")
if "v2/gates/verify_status_reporting_active.py" not in sr.get("verification",[]) or "v2/tests/test_status_reporting_active_fail_closed.py" not in sr.get("verification",[]):e.append("registry verification binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov.get("entries",[])}
if ce.get("OPS-STATUS-REPORTING-001",{}).get("coverage_status")!="MACHINE_ENFORCED":e.append("machine coverage missing")
ad=d.get("adoption",{})
if ad.get("decision")!="OPS-STATUS-REPORTING-001を採用して進めて" or ad.get("independent_review_run_id")!=36838019914:e.append("adoption evidence invalid")
if e:
 print("CB6 STATUS REPORTING ACTIVE FAIL:")
 for x in e:print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING ACTIVE PASS: all33+future; Japanese tags; classes=3; registry+coverage+adoption evidence enforced")
