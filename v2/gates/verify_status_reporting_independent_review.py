#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
c=json.loads((R/"v2/gates/status_reporting_contract_v3.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v2.json").read_text(encoding="utf-8"))
r=json.loads((R/"v2/gates/operational_rule_registry_v5.json").read_text(encoding="utf-8"))
if c.get("schema")!=3 or c.get("rule_id")!="OPS-STATUS-REPORTING-001" or c.get("status")!="CANDIDATE": e.append("status reporting v3 candidate identity/status invalid")
if c.get("revision",{}).get("from")!="v2/gates/status_reporting_contract_v2.json" or c.get("revision",{}).get("supersedes")!="v2/gates/status_reporting_contract_v2.json": e.append("v3 lineage invalid")
if c.get("allowed_classifications")!=["進めて推奨","待ち","スマホ操作が必要"]: e.append("classification contract changed")
fields=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]
if c.get("required_report_fields")!=fields: e.append("four-line fields invalid")
t=c.get("four_line_template",{}); expected={"分類":"進めて推奨","次にユーザーがすること":"「進めて」","ChatGPTアプリ":"閉じてOK","スマホ操作":"不要。再試行もしなくて大丈夫です。"}
if t.get("required") is not True or t.get("state_consistency_required") is not True or t.get("no_user_operation_form")!=expected: e.append("four-line template invalid")
if c.get("activation",{}).get("direct_active_forbidden") is not True: e.append("candidate allows direct activation")
if a.get("schema")!=2 or a.get("status")!="ACTIVE": e.append("ACTIVE v2 authority changed")
rules={x.get("id"):x for x in r.get("rules",[])}; sr=rules.get("OPS-STATUS-REPORTING-001",{})
if sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v2.json": e.append("ACTIVE registry binding changed")
if e:
 print("CB6 STATUS REPORTING V3 INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V3 INDEPENDENT REVIEW PASS: four-line candidate verified; ACTIVE v2 and registry v5 authority unchanged; direct activation blocked")
