#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_status_reporting_v13_independent_review.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("v13 independent baseline failed")
cases=[
("missing-cumulative",lambda d:d["wait_final_summary"].update({"exact_order_required":["分類","次回確認目安","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]})),
("wrong-order",lambda d:d["wait_final_summary"].update({"exact_order_required":["分類","次回確認目安","累積経過時間","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]})),
("not-terminal",lambda d:d["wait_final_summary"].update({"must_be_response_end":False})),
("allow-duplicate",lambda d:d["wait_final_summary"].update({"duplicate_information_forbidden":False})),
("reset-elapsed",lambda d:d["preservation"].update({"cumulative_elapsed_no_reset_preserved":False})),
("unsupported-next-check",lambda d:d["preservation"].update({"evidence_based_next_check_preserved":False})),
("lose-duration-unknown",lambda d:d["preservation"].update({"duration_unknown_behavior_preserved":False})),
("change-non-wait",lambda d:d["preservation"].update({"non_wait_four_line_summary_preserved":False})),
("allow-registry-change",lambda d:d["non_interference"].update({"registry_coverage_change_forbidden":False})),
("allow-auditor-change",lambda d:d["non_interference"].update({"auditor_v2_change_forbidden":False})),
("direct-active",lambda d:d["activation"].update({"direct_active_forbidden":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/status_reporting_contract_candidate_v13.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("v13 independent bypass passed:"+name)
  print("PASS expected independent rejection:",name)
print("CB6 STATUS REPORTING V13 INDEPENDENT DESTRUCTIVE PASS:",len(cases))
