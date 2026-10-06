#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v13.json").read_text())
a=json.loads((R/"v2/gates/status_reporting_contract_v12.json").read_text())
if d.get("schema")!=13 or d.get("status")!="CANDIDATE" or d.get("extends")!="v2/gates/status_reporting_contract_v12.json":e.append("candidate identity/basis")
if a.get("schema")!=12 or a.get("status")!="ACTIVE":e.append("ACTIVE v12 basis")
w=d.get("wait_final_summary",{});order=["分類","累積経過時間","次回確認目安","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]
if w.get("required") is not True or w.get("classification")!="待ち" or w.get("exact_order_required")!=order or w.get("must_be_response_end") is not True:e.append("wait six-line terminal summary")
p=d.get("preservation",{})
for k in ("active_v12_unchanged","run_start_basis_preserved","cumulative_elapsed_no_reset_preserved","evidence_based_next_check_preserved","duration_unknown_behavior_preserved","non_wait_four_line_summary_preserved"):
 if p.get(k) is not True:e.append("preservation:"+k)
n=d.get("non_interference",{})
for k in ("registry_coverage_change_forbidden","auditor_v2_change_forbidden","method_freeze_change_forbidden","development_gate_change_forbidden","signal_convenience_application_behavior_change_forbidden"):
 if n.get(k) is not True:e.append("non-interference:"+k)
if d.get("activation",{}).get("direct_active_forbidden") is not True:e.append("direct ACTIVE")
if e:
 print("CB6 STATUS REPORTING V13 CANDIDATE FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("CB6 STATUS REPORTING V13 CANDIDATE PASS")
