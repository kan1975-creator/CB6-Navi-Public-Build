#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];c=json.loads((R/"v2/gates/cross_cutting_rule_foundation_candidate.json").read_text());e=[]
if c.get("status")!="PROPOSED" or c.get("candidate_id")!="CB6-CROSS-CUTTING-RULE-FOUNDATION-001":e.append("candidate identity/status invalid")
s=c.get("scope",{})
for k in ("all_current_features","all_future_features","all_33_consolidated_items","derivative_work"):
 if s.get(k) is not True:e.append("scope weakened: "+k)
if s.get("feature_opt_in_required") is not False or s.get("feature_override_may_weaken") is not False:e.append("cross-cutting inheritance can be bypassed")
rules={x["id"]:x for x in c.get("rules",[])}
for rid in ("OPS-STATUS-REPORTING-001","NOTIFICATION-STALE-STATE","OPS-USER-APPROVAL-BEFORE-FIX-001"):
 if rules.get(rid,{}).get("required_classification")!="CROSS_CUTTING":e.append("missing cross-cutting classification: "+rid)
a=c.get("approval_semantics",{})
for k in ("investigation_and_read_only_distinct_from_fix_approval","exact_change_binding_required","reuse_for_different_change_forbidden","post_hoc_forbidden","missing_approval_forbidden"):
 if a.get(k) is not True:e.append("approval semantics weakened: "+k)
f=c.get("feature_contract_inheritance",{})
if f.get("automatic") is not True or f.get("required_value")!="ALL_ACTIVE_CROSS_CUTTING_RULES" or f.get("new_feature_must_inherit_without_per_rule_wiring") is not True:e.append("feature inheritance invalid")
wl=(R/"v2/governance/consolidated_worklist_2026-09-30.md").read_text();nums={int(x) for x in re.findall(r'^(\d+)\.\s+\*\*',wl,re.M)}
if nums!=set(range(1,34)):e.append("33-item worklist not complete")
reg=json.loads((R/"v2/gates/operational_rule_registry_v3.json").read_text());rr={x["id"]:x for x in reg["rules"]}
if rr["OPS-STATUS-REPORTING-001"]["status"]!="ACTIVE":e.append("status rule active authority drift")
if rr["NOTIFICATION-STALE-STATE"]["status"]!="ACTIVE" or rr["OPS-USER-APPROVAL-BEFORE-FIX-001"]["status"]!="ACTIVE":e.append("delegated active rule status drift")
if c.get("lifecycle",{}).get("direct_active_forbidden") is not True:e.append("direct active allowed")
if e:
 print("CB6 CROSS-CUTTING FOUNDATION CANDIDATE FAIL:")
 for x in e:print(" -",x)
 raise SystemExit(1)
print("CB6 CROSS-CUTTING FOUNDATION CANDIDATE PASS: all33/current/future; inheritance=automatic; current ACTIVE authority aligned")
