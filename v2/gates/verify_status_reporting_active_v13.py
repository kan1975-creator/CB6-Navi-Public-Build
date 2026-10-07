#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v13.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v12.json").read_text(encoding="utf-8"))
if d.get("schema")!=13 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE":e.append("ACTIVE v13 identity/status")
if a.get("schema")!=12 or a.get("status")!="ACTIVE":e.append("v12 basis not preserved")
if d.get("extends")!="v2/gates/status_reporting_contract_v12.json":e.append("v12 extension binding")
w=d.get("wait_final_summary",{})
if w.get("required") is not True or w.get("classification")!="待ち" or w.get("exact_order_required")!=["分類","累積経過時間","次回確認目安","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]:e.append("wait six-line summary")
for k in ("must_be_response_end","duplicate_information_forbidden"):
 if w.get(k) is not True:e.append("wait summary:"+k)
p=d.get("preservation",{})
for k in ("active_v12_unchanged","run_start_basis_preserved","cumulative_elapsed_no_reset_preserved","evidence_based_next_check_preserved","duration_unknown_behavior_preserved","non_wait_four_line_summary_preserved"):
 if p.get(k) is not True:e.append("preservation:"+k)
n=d.get("non_interference",{})
for k in ("registry_coverage_change_forbidden","auditor_v2_change_forbidden","method_freeze_change_forbidden","development_gate_change_forbidden","signal_convenience_application_behavior_change_forbidden"):
 if n.get(k) is not True:e.append("non-interference:"+k)
x=d.get("activation",{})
if x.get("status")!="ACTIVE" or x.get("candidate_validation_run_id")!=37550233646 or x.get("independent_review_run_id")!=37559089448:e.append("activation evidence")
if d.get("adoption",{}).get("status")!="ADOPTED":e.append("adoption")
ev=json.loads((R/"v2/gates/status_reporting_adoption_evidence_v13.json").read_text(encoding="utf-8"))
if ev.get("status")!="ACTIVE":e.append("adoption evidence status")
if e:
 print("CB6 STATUS REPORTING V13 ACTIVE FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("CB6 STATUS REPORTING V13 ACTIVE PASS: v12 basis preserved; wait six-line terminal summary and timing evidence are adopted and evidence-bound")
