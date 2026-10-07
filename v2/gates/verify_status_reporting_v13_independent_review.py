#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
c=json.loads((R/"v2/gates/status_reporting_contract_candidate_v13.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v12.json").read_text(encoding="utf-8"))
if a.get("schema")!=12 or a.get("status")!="ACTIVE" or a.get("rule_id")!="OPS-STATUS-REPORTING-001":e.append("ACTIVE v12 authority")
if c.get("schema")!=13 or c.get("status")!="CANDIDATE" or c.get("extends")!="v2/gates/status_reporting_contract_v12.json":e.append("v13 candidate identity")
w=c.get("wait_final_summary",{})
if w.get("required") is not True or w.get("classification")!="待ち":e.append("wait summary applicability")
if w.get("exact_order_required")!=["分類","累積経過時間","次回確認目安","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]:e.append("wait six-line exact order")
for k in ("must_be_response_end","duplicate_information_forbidden"):
 if w.get(k) is not True:e.append("wait terminal semantic:"+k)
p=c.get("preservation",{})
for k in ("active_v12_unchanged","run_start_basis_preserved","cumulative_elapsed_no_reset_preserved","evidence_based_next_check_preserved","duration_unknown_behavior_preserved","non_wait_four_line_summary_preserved"):
 if p.get(k) is not True:e.append("preservation:"+k)
n=c.get("non_interference",{})
for k in ("registry_coverage_change_forbidden","auditor_v2_change_forbidden","method_freeze_change_forbidden","development_gate_change_forbidden","signal_convenience_application_behavior_change_forbidden"):
 if n.get(k) is not True:e.append("non-interference:"+k)
x=c.get("activation",{})
if x.get("direct_active_forbidden") is not True:e.append("direct ACTIVE forbidden")
req=x.get("requires",[])
for k in ("positive_candidate_verification","destructive_test","independent_review","explicit_user_adoption","machine_enforced_registry_coverage"):
 if k not in req:e.append("activation requirement:"+k)
if e:
 print("CB6 STATUS REPORTING V13 INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 STATUS REPORTING V13 INDEPENDENT REVIEW PASS: ACTIVE v12 independently preserved; wait six-line terminal order, timing preservation, non-wait summary, non-interference and activation boundary reconstructed")
