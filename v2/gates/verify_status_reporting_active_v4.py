#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v4.json").read_text(encoding="utf-8"))
if d.get("schema")!=4 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v4 identity/status invalid")
fields=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]
if d.get("required_report_fields")!=fields: e.append("four-line fields invalid")
t=d.get("four_line_template",{})
if t.get("placement")!="FINAL_FOUR_LINES" or t.get("final_four_lines_required") is not True or t.get("order_exactly_required")!=fields or t.get("content_after_four_lines_forbidden") is not True: e.append("final four-line placement invalid")
s=d.get("rules",{}).get("スマホ操作が必要",{}); f=s.get("final_user_action_section",{}); fc=s.get("fail_closed",{})
if f.get("required") is not True or f.get("heading")!="あなたが今すること" or f.get("concrete_steps_required") is not True or f.get("generic_device_instruction_forbidden") is not True: e.append("smartphone action section invalid")
if fc.get("required") is not True or fc.get("if_concrete_operation_not_identified")!="DO_NOT_CLASSIFY_AS_SMARTPHONE_ACTION_REQUIRED": e.append("smartphone fail-closed invalid")
reg=json.loads((R/"v2/gates/operational_rule_registry_v7.json").read_text()); rules={x.get("id"):x for x in reg.get("rules",[])}; sr=rules.get("OPS-STATUS-REPORTING-001",{})
if reg.get("version")!=7 or sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v4.json": e.append("registry v7 active binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov.get("entries",[])}
if cov.get("registry")!="v2/gates/operational_rule_registry_v7.json" or ce.get("OPS-STATUS-REPORTING-001",{}).get("coverage_status")!="MACHINE_ENFORCED": e.append("machine coverage v7 missing")
ad=d.get("adoption",{})
if ad.get("candidate_validation_run_id")!=36988836384 or ad.get("independent_review_run_id")!=36996374433 or ad.get("independent_review_head")!="57a834424005c15f45935cfc2a52fc1ed6935938": e.append("v4 adoption evidence invalid")
if e:
 print("CB6 STATUS REPORTING V4 ACTIVE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V4 ACTIVE PASS: final-four-line + concrete smartphone action; registry v7+coverage+adoption enforced")
