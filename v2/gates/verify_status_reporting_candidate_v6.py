#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v6.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v5.json").read_text(encoding="utf-8"))
if d.get("schema")!=6 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v6 identity/status invalid")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope","rules","freshness_rule","fix_approval_boundary","report_tags"):
 if d.get(k)!=a.get(k): e.append("existing v5 contract changed: "+k)
f=d.get("final_summary_display",{})
if f.get("placement")!="REPORT_END" or f.get("markdown_bullet_and_bold_required") is not True or f.get("duplicate_information_forbidden") is not True: e.append("final summary display rule invalid")
if f.get("non_wait_fields")!=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]: e.append("non-wait final fields invalid")
if f.get("wait_additional_fields")!=["累積経過時間","次回確認目安"] or f.get("wait_additional_fields_only_when_classification")!="待ち": e.append("wait final fields invalid")
if f.get("preserve_v5_wait_time_calculation_rules") is not True or d["rules"]["待ち"]["wait_time_display"]!=a["rules"]["待ち"]["wait_time_display"]: e.append("v5 wait timing changed")
if f.get("content_after_final_summary_forbidden") is not True: e.append("content after final summary allowed")
if d.get("activation",{}).get("direct_active_forbidden") is not True or d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V6 CANDIDATE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V6 CANDIDATE PASS: final bullet+bold summary, no duplicate information, wait timing shown at report end; ACTIVE v5 behavior preserved")
