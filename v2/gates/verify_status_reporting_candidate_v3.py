#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2]; d=json.loads((R/"v2/gates/status_reporting_contract_v3.json").read_text(encoding="utf-8")); e=[]
if d.get("schema")!=3 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE":e.append("candidate v3 identity/status invalid")
if d.get("revision",{}).get("from")!="v2/gates/status_reporting_contract_v2.json" or d.get("revision",{}).get("supersedes")!="v2/gates/status_reporting_contract_v2.json" or not d.get("revision",{}).get("reason"):e.append("v3 revision lineage invalid")
if d.get("allowed_classifications")!=["進めて推奨","待ち","スマホ操作が必要"] or d.get("exactly_one_classification_required") is not True:e.append("classification contract invalid")
fields=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]
if d.get("required_report_fields")!=fields:e.append("four-line required fields invalid")
t=d.get("four_line_template",{}); form=t.get("no_user_operation_form",{})
if t.get("required") is not True or t.get("state_consistency_required") is not True:e.append("four-line enforcement flags invalid")
if [t.get("classification_field"),t.get("next_user_action_field"),t.get("chatgpt_app_field"),t.get("smartphone_action_field")]!=fields:e.append("four-line field mapping invalid")
expected={"分類":"進めて推奨","次にユーザーがすること":"「進めて」","ChatGPTアプリ":"閉じてOK","スマホ操作":"不要。再試行もしなくて大丈夫です。"}
if form!=expected:e.append("canonical no-user-operation form invalid")
w=d.get("rules",{}).get("待ち",{}); wi=w.get("post_wait_user_instruction",{})
if "post_wait_user_instruction" not in w.get("required_fields",[]) or wi.get("required") is not True:e.append("v2 post-wait rule lost")
s=d.get("scope",{}); wl=R/s.get("consolidated_worklist","")
for k in ("all_33_items_mandatory","applies_to_all_derivative_work","applies_to_all_future_work","applies_to_unknown_future_features_without_enumeration"):
 if s.get(k) is not True:e.append("scope weakened: "+k)
if not wl.is_file():e.append("worklist missing")
else:
 nums={int(x) for x in re.findall(r'^(\d+)\.\s+',wl.read_text(encoding="utf-8"),re.M)}
 if set(range(1,34))-nums:e.append("worklist missing item(s) 1..33")
active=json.loads((R/"v2/gates/status_reporting_contract_v2.json").read_text(encoding="utf-8"))
if active.get("status")!="ACTIVE" or active.get("schema")!=2:e.append("ACTIVE v2 was not preserved")
if e:
 print("CB6 STATUS REPORTING V3 CANDIDATE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V3 CANDIDATE PASS: four-line template; v2 preserved; all33+future scope preserved")
