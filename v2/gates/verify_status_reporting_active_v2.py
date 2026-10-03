#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];d=json.loads((R/"v2/gates/status_reporting_contract_v2.json").read_text(encoding="utf-8"));e=[]
if d.get("schema")!=2 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE":e.append("active v2 identity/status invalid")
s=d.get("scope",{}); wl=R/s.get("consolidated_worklist","")
for k in ("all_33_items_mandatory","applies_to_all_derivative_work","applies_to_all_future_work","applies_to_unknown_future_features_without_enumeration"):
 if s.get(k) is not True:e.append("scope weakened: "+k)
if not wl.is_file():e.append("worklist missing")
else:
 nums={int(x) for x in re.findall(r'^(\d+)\.\s+',wl.read_text(encoding="utf-8"),re.M)}
 if set(range(1,34))-nums:e.append("worklist missing item(s) 1..33")
if d.get("allowed_classifications")!=["進めて推奨","待ち","スマホ操作が必要"]:e.append("classification invalid")
w=d.get("rules",{}).get("待ち",{}); wi=w.get("post_wait_user_instruction",{})
if "post_wait_user_instruction" not in w.get("required_fields",[]) or wi.get("required") is not True or "進めて" not in wi.get("when_user_instruction_needed","") or wi.get("when_automatic_monitoring_active")!="指示不要・自動モニタリング継続":e.append("post-wait instruction invalid")
reg=json.loads((R/"v2/gates/operational_rule_registry_v5.json").read_text()); rules={x.get("id"):x for x in reg.get("rules",[])}; sr=rules.get("OPS-STATUS-REPORTING-001",{})
if sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v2.json":e.append("registry v5 active binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov.get("entries",[])}
if cov.get("registry")!="v2/gates/operational_rule_registry_v5.json" or ce.get("OPS-STATUS-REPORTING-001",{}).get("coverage_status")!="MACHINE_ENFORCED":e.append("machine coverage v5 missing")
ad=d.get("adoption",{})
if ad.get("independent_review_run_id")!=36952667256 or ad.get("candidate_validation_run_id")!=36951709218:e.append("v2 adoption evidence invalid")
if e:
 print("CB6 STATUS REPORTING V2 ACTIVE FAIL:")
 for x in e:print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V2 ACTIVE PASS: all33+future; post-wait instruction; registry v5+coverage+adoption enforced")
