#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v4.json").read_text(encoding="utf-8"))
if d.get("schema")!=4 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v4 identity/status invalid")
rev=d.get("revision",{})
if rev.get("from")!="v2/gates/status_reporting_contract_v3.json" or rev.get("supersedes")!="v2/gates/status_reporting_contract_v3.json" or not rev.get("reason"): e.append("v4 revision lineage invalid")
if d.get("allowed_classifications")!=["進めて推奨","待ち","スマホ操作が必要"] or d.get("exactly_one_classification_required") is not True: e.append("classification contract invalid")
fields=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]
if d.get("required_report_fields")!=fields: e.append("four-line fields invalid")
s=d.get("rules",{}).get("スマホ操作が必要",{}); f=s.get("final_user_action_section",{}); fc=s.get("fail_closed",{})
for x in ("required_device_action","required_evidence","final_user_action_section"):
 if x not in s.get("required_fields",[]): e.append("smartphone required field missing: "+x)
if f.get("required") is not True or f.get("heading")!="あなたが今すること" or f.get("placement")!="REPORT_END" or f.get("concrete_steps_required") is not True or f.get("generic_device_instruction_forbidden") is not True: e.append("final user action section invalid")
needed=["target_apk_or_build","operation_target","location_and_zoom_or_equivalent_test_condition","what_to_verify","evidence_to_return"]
if f.get("include_when_known")!=needed: e.append("concrete smartphone detail list invalid")
if fc.get("required") is not True or fc.get("if_concrete_operation_not_identified")!="DO_NOT_CLASSIFY_AS_SMARTPHONE_ACTION_REQUIRED" or fc.get("assistant_must_identify_operation_first") is not True: e.append("smartphone fail-closed rule invalid")
scope=d.get("scope",{}); wl=R/scope.get("consolidated_worklist","")
for k in ("all_33_items_mandatory","applies_to_all_derivative_work","applies_to_all_future_work","applies_to_unknown_future_features_without_enumeration"):
 if scope.get(k) is not True: e.append("scope weakened: "+k)
if not wl.is_file(): e.append("worklist missing")
else:
 nums={int(x) for x in re.findall(r'^(\d+)\.\s+',wl.read_text(encoding="utf-8"),re.M)}
 if set(range(1,34))-nums: e.append("worklist missing item(s) 1..33")
a=json.loads((R/"v2/gates/status_reporting_contract_v3.json").read_text(encoding="utf-8"))
reg=json.loads((R/"v2/gates/operational_rule_registry_v6.json").read_text(encoding="utf-8")); rules={x.get("id"):x for x in reg.get("rules",[])}
if a.get("schema")!=3 or a.get("status")!="ACTIVE": e.append("ACTIVE v3 was not preserved")
if rules.get("OPS-STATUS-REPORTING-001",{}).get("contract")!="v2/gates/status_reporting_contract_v3.json": e.append("ACTIVE registry v6 binding changed")
if d.get("activation",{}).get("direct_active_forbidden") is not True: e.append("candidate allows direct activation")
if e:
 print("CB6 STATUS REPORTING V4 CANDIDATE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V4 CANDIDATE PASS: concrete report-end smartphone steps required; unidentified operations fail closed; ACTIVE v3 preserved")
