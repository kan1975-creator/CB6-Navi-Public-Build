#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2]; d=json.loads((R/"v2/gates/status_reporting_contract_v3.json").read_text(encoding="utf-8")); e=[]
if d.get("schema")!=3 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v3 identity/status invalid")
if d.get("allowed_classifications")!=["進めて推奨","待ち","スマホ操作が必要"] or d.get("exactly_one_classification_required") is not True: e.append("classification invalid")
fields=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]
if d.get("required_report_fields")!=fields: e.append("four-line fields invalid")
t=d.get("four_line_template",{}); expected={"分類":"進めて推奨","次にユーザーがすること":"「進めて」","ChatGPTアプリ":"閉じてOK","スマホ操作":"不要。再試行もしなくて大丈夫です。"}
if t.get("required") is not True or t.get("state_consistency_required") is not True or t.get("no_user_operation_form")!=expected: e.append("four-line template invalid")
s=d.get("scope",{}); wl=R/s.get("consolidated_worklist","")
for k in ("all_33_items_mandatory","applies_to_all_derivative_work","applies_to_all_future_work","applies_to_unknown_future_features_without_enumeration"):
 if s.get(k) is not True:e.append("scope weakened: "+k)
if not wl.is_file():e.append("worklist missing")
else:
 nums={int(x) for x in re.findall(r'^(\d+)\.\s+',wl.read_text(encoding="utf-8"),re.M)}
 if set(range(1,34))-nums:e.append("worklist missing item(s) 1..33")
w=d.get("rules",{}).get("待ち",{}); wi=w.get("post_wait_user_instruction",{})
if "post_wait_user_instruction" not in w.get("required_fields",[]) or wi.get("required") is not True:e.append("post-wait instruction invalid")
reg=json.loads((R/"v2/gates/operational_rule_registry_v6.json").read_text()); rules={x.get("id"):x for x in reg.get("rules",[])}; sr=rules.get("OPS-STATUS-REPORTING-001",{})
if sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v3.json":e.append("registry v6 active binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov.get("entries",[])}
if cov.get("registry")!="v2/gates/operational_rule_registry_v6.json" or ce.get("OPS-STATUS-REPORTING-001",{}).get("coverage_status")!="MACHINE_ENFORCED":e.append("machine coverage v6 missing")
ad=d.get("adoption",{})
if ad.get("candidate_validation_run_id")!=36975550390 or ad.get("independent_review_run_id")!=36976511431 or ad.get("independent_review_head")!="aaaf68ecea9bc8e4e7069cf9832ea1b79a28163b":e.append("v3 adoption evidence invalid")
if e:
 print("CB6 STATUS REPORTING V3 ACTIVE FAIL:")
 for x in e:print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V3 ACTIVE PASS: mandatory four-line template; all33+future; registry v6+coverage+adoption enforced")
