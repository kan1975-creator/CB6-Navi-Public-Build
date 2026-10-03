#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v6.json").read_text(encoding="utf-8"))
v5=json.loads((R/"v2/gates/status_reporting_contract_v5.json").read_text(encoding="utf-8"))
if d.get("schema")!=6 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v6 identity/status invalid")
for k in ("allowed_classifications","exactly_one_classification_required","required_report_fields","four_line_template","scope","rules","freshness_rule","fix_approval_boundary","report_tags"):
 if d.get(k)!=v5.get(k): e.append("existing ACTIVE v5 contract changed: "+k)
f=d.get("final_summary_display",{})
if f.get("placement")!="REPORT_END" or f.get("markdown_bullet_and_bold_required") is not True or f.get("duplicate_information_forbidden") is not True: e.append("v6 final summary display invalid")
if f.get("non_wait_fields")!=["分類","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]: e.append("v6 non-wait fields invalid")
if f.get("wait_additional_fields")!=["累積経過時間","次回確認目安"] or f.get("wait_additional_fields_only_when_classification")!="待ち": e.append("v6 wait final fields invalid")
if f.get("preserve_v5_wait_time_calculation_rules") is not True or d["rules"]["待ち"]["wait_time_display"]!=v5["rules"]["待ち"]["wait_time_display"]: e.append("ACTIVE v5 wait timing changed")
if f.get("content_after_final_summary_forbidden") is not True: e.append("v6 content after final summary allowed")
reg=json.loads((R/"v2/gates/operational_rule_registry_v9.json").read_text()); rules={x.get("id"):x for x in reg.get("rules",[])}; sr=rules.get("OPS-STATUS-REPORTING-001",{})
if reg.get("version")!=9 or sr.get("status")!="ACTIVE" or sr.get("contract")!="v2/gates/status_reporting_contract_v6.json": e.append("registry v9 active binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov.get("entries",[])}
if cov.get("registry")!="v2/gates/operational_rule_registry_v9.json" or ce.get("OPS-STATUS-REPORTING-001",{}).get("coverage_status")!="MACHINE_ENFORCED": e.append("machine coverage v9 missing")
ad=d.get("adoption",{})
if ad.get("candidate_validation_run_id")!=37127414539 or ad.get("independent_review_run_id")!=37127629654 or ad.get("independent_review_head")!="9c48e9af261498d0c290665cb2549d18a0bbf2be": e.append("v6 adoption evidence invalid")
if e:
 print("CB6 STATUS REPORTING V6 ACTIVE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 STATUS REPORTING V6 ACTIVE PASS: final-summary display + v5 wait timing preserved; registry v9+coverage+adoption enforced")
