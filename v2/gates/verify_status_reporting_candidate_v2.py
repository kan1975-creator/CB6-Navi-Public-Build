#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v2.json").read_text(encoding="utf-8"));e=[]
if d.get("schema")!=2 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE":e.append("candidate identity/status invalid")
s=d.get("scope",{});wl=R/s.get("consolidated_worklist","")
if s.get("type")!="CB6_PROJECT_WIDE_CROSS_CUTTING":e.append("scope not project-wide")
for k in ("all_33_items_mandatory","applies_to_all_derivative_work","applies_to_all_future_work","applies_to_unknown_future_features_without_enumeration"):
 if s.get(k) is not True:e.append("scope weakened: "+k)
if s.get("consolidated_worklist_required_item_count")!=33:e.append("33-item requirement missing")
if not wl.is_file():e.append("worklist missing")
else:
 nums={int(x) for x in re.findall(r'^(\d+)\.\s+',wl.read_text(encoding="utf-8"),re.M)}
 if set(range(1,34))-nums:e.append("worklist missing item(s) 1..33")
if s.get("feature_specific_override_may_weaken_or_disable") is not False:e.append("feature override may weaken")
if s.get("new_feature_requires_explicit_opt_in") is not False:e.append("future work requires opt-in")
tags=d.get("report_tags",{})
if tags.get("required_at_report_start") is not True:e.append("report tag not required at start")
if tags.get("allowed")!=["ガバナンス","信号機","コンビニ","その他"]:e.append("report tag vocabulary invalid")
if tags.get("multiple_tags_allowed_for_cross_domain_report") is not True:e.append("cross-domain multiple tags forbidden")
if tags.get("governance_report_requires")!="ガバナンス":e.append("Governance tag not mandatory for governance report")
if tags.get("tag_presence_does_not_replace_status_classification") is not True:e.append("tag incorrectly replaces status classification")
m=tags.get("domain_mapping",{})
if m!={"governance":"ガバナンス","signal":"信号機","convenience":"コンビニ","unknown_or_other":"その他"}:e.append("report tag domain mapping invalid")
expected=["進めて推奨","待ち","スマホ操作が必要"]
if d.get("allowed_classifications")!=expected or d.get("exactly_one_classification_required") is not True:e.append("classification invalid")
r=d.get("rules",{})
if set(r)!=set(expected):e.append("classification keys mismatch")
if r.get("進めて推奨",{}).get("chat_instruction_wait_alone_forbidden") is not True:e.append("chat wait allowed")
if r.get("待ち",{}).get("required_fields")!=["approximate_wait_time","next_check_timing","parallel_work_available","post_wait_user_instruction"] or r.get("待ち",{}).get("parallel_read_only_work_allowed") is not True:e.append("wait invalid")
wi=r.get("待ち",{}).get("post_wait_user_instruction",{})
if wi.get("required") is not True or "進めて" not in wi.get("when_user_instruction_needed","") or wi.get("when_automatic_monitoring_active")!="指示不要・自動モニタリング継続":e.append("post-wait instruction invalid")
if r.get("スマホ操作が必要",{}).get("required_fields")!=["required_device_action","required_evidence"]:e.append("device invalid")
f=d.get("freshness_rule",{})
for k in ("progress_query_requires_current_head","progress_query_requires_relevant_run","material_log_evidence_requires_fresh_raw_log"):
 if f.get(k) is not True:e.append("freshness weakened: "+k)
if f.get("delegates_stale_state_authority_to")!="v2/gates/notification_stale_state.json" or not (R/f.get("delegates_stale_state_authority_to","")).is_file():e.append("stale delegation invalid")
a=d.get("fix_approval_boundary",{})
if a.get("delegates_to")!="OPS-USER-APPROVAL-BEFORE-FIX-001":e.append("approval delegation invalid")
for k in ("investigation_permission_is_not_fix_permission","generic_progress_permission_is_not_specific_fix_approval","old_approval_reuse_for_different_change_forbidden"):
 if a.get(k) is not True:e.append("approval boundary weakened: "+k)
reg=json.loads((R/"v2/gates/operational_rule_registry_v3.json").read_text(encoding="utf-8"));ids={x.get("id"):x for x in reg.get("rules",[])}
if ids.get(a.get("delegates_to"),{}).get("status")!="ACTIVE":e.append("approval target not ACTIVE")
ac=d.get("activation",{})
if ac.get("direct_active_forbidden") is not True:e.append("direct activation allowed")
if set(ac.get("requires",[]))!={"positive_verification","destructive_test","successful_github_run_evidence","independent_review","explicit_user_adoption","machine_enforced_coverage"}:e.append("activation requirements invalid")
if e:
 print("CB6 STATUS REPORTING CANDIDATE FAIL:")
 for x in e:print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING CANDIDATE PASS: all33+derivatives+future; classes=3; freshness+approval boundaries enforced")
