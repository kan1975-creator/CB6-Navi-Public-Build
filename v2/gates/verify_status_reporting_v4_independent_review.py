#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
c=json.loads((R/"v2/gates/status_reporting_contract_candidate_v4.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v3.json").read_text(encoding="utf-8"))
r=json.loads((R/"v2/gates/operational_rule_registry_v6.json").read_text(encoding="utf-8"))
if c.get("schema")!=4 or c.get("rule_id")!="OPS-STATUS-REPORTING-001" or c.get("status")!="CANDIDATE": e.append("status reporting v4 candidate identity/status invalid")
rev=c.get("revision",{})
if rev.get("from")!="v2/gates/status_reporting_contract_v3.json" or rev.get("supersedes")!="v2/gates/status_reporting_contract_v3.json": e.append("v4 lineage invalid")
fields=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]
if c.get("required_report_fields")!=fields: e.append("four-line fields invalid")
t=c.get("four_line_template",{})
if t.get("placement")!="FINAL_FOUR_LINES" or t.get("final_four_lines_required") is not True or t.get("order_exactly_required")!=fields or t.get("content_after_four_lines_forbidden") is not True: e.append("final four-line placement invalid")
s=c.get("rules",{}).get("スマホ操作が必要",{}); f=s.get("final_user_action_section",{}); fc=s.get("fail_closed",{})
if f.get("required") is not True or f.get("heading")!="あなたが今すること" or f.get("concrete_steps_required") is not True or f.get("generic_device_instruction_forbidden") is not True: e.append("smartphone action section invalid")
if fc.get("required") is not True or fc.get("if_concrete_operation_not_identified")!="DO_NOT_CLASSIFY_AS_SMARTPHONE_ACTION_REQUIRED" or fc.get("assistant_must_identify_operation_first") is not True: e.append("smartphone fail-closed invalid")
if c.get("activation",{}).get("direct_active_forbidden") is not True: e.append("candidate allows direct activation")
if a.get("schema")!=3 or a.get("status")!="ACTIVE": e.append("ACTIVE v3 authority changed")
rules={x.get("id"):x for x in r.get("rules",[])}; sr=rules.get("OPS-STATUS-REPORTING-001",{})
if sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v3.json": e.append("ACTIVE registry v6 binding changed")
if e:
 print("CB6 STATUS REPORTING V4 INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V4 INDEPENDENT REVIEW PASS: final-four-line and smartphone-action candidate verified; ACTIVE v3 and registry v6 authority preserved; direct activation blocked")
