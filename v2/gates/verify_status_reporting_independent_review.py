#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
c=json.loads((R/"v2/gates/status_reporting_contract_candidate_v2.json").read_text(encoding="utf-8"))
m=json.loads((R/"v2/gates/status_reporting_method_revision_candidate.json").read_text(encoding="utf-8"))
r=json.loads((R/"v2/gates/operational_rule_registry_v4.json").read_text(encoding="utf-8"))
if c.get("rule_id")!="OPS-STATUS-REPORTING-001" or c.get("status")!="CANDIDATE": e.append("status reporting candidate identity/status invalid")
if c.get("scope",{}).get("all_33_items_mandatory") is not True: e.append("33-item scope weakened")
if c.get("scope",{}).get("applies_to_all_future_work") is not True or c.get("scope",{}).get("applies_to_unknown_future_features_without_enumeration") is not True: e.append("future scope weakened")
if c.get("allowed_classifications")!=["進めて推奨","待ち","スマホ操作が必要"]: e.append("classification contract changed")
t=c.get("report_tags",{})
if t.get("allowed")!=["ガバナンス","信号機","コンビニ","その他"] or t.get("required_at_report_start") is not True or t.get("governance_report_requires")!="ガバナンス": e.append("Japanese report tag contract invalid")
if c.get("activation",{}).get("direct_active_forbidden") is not True: e.append("candidate allows direct activation")
w=c.get("rules",{}).get("待ち",{}); wi=w.get("post_wait_user_instruction",{})
if "post_wait_user_instruction" not in w.get("required_fields",[]) or wi.get("required") is not True or "進めて" not in wi.get("when_user_instruction_needed","") or wi.get("when_automatic_monitoring_active")!="指示不要・自動モニタリング継続": e.append("post-wait instruction requirement invalid")
rules={x.get("id"):x for x in r.get("rules",[])}
if rules.get("OPS-STATUS-REPORTING-001",{}).get("status")!="ACTIVE": e.append("active registry authority changed")
if m.get("status")!="PROPOSED" or m.get("invariants",{}).get("prechange_authority_remains_authoritative_until_adoption") is not True or m.get("invariants",{}).get("candidate_cannot_self_adopt") is not True: e.append("method revision pre-adoption protection invalid")
if e:
 print("CB6 STATUS REPORTING INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING INDEPENDENT REVIEW PASS: candidate scope/classes/Japanese tags preserved; ACTIVE authority unchanged; post-wait instruction independently verified; self-adoption blocked")
