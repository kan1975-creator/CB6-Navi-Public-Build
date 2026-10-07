#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_status_reporting_active_v13.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("v13 ACTIVE baseline failed")
cases=[
("inactive",lambda d:d.update({"status":"CANDIDATE"})),
("missing-cumulative",lambda d:d["wait_final_summary"].update({"exact_order_required":["分類","次回確認目安","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]})),
("wrong-order",lambda d:d["wait_final_summary"].update({"exact_order_required":["分類","次回確認目安","累積経過時間","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]})),
("nonterminal",lambda d:d["wait_final_summary"].update({"must_be_response_end":False})),
("reset-elapsed",lambda d:d["preservation"].update({"cumulative_elapsed_no_reset_preserved":False})),
("unsupported-next-check",lambda d:d["preservation"].update({"evidence_based_next_check_preserved":False})),
("lose-duration-unknown",lambda d:d["preservation"].update({"duration_unknown_behavior_preserved":False})),
("change-non-wait",lambda d:d["preservation"].update({"non_wait_four_line_summary_preserved":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/status_reporting_contract_v13.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("v13 ACTIVE destructive bypass:"+name)
  print("PASS expected ACTIVE rejection:",name)
print("CB6 STATUS REPORTING V13 ACTIVE DESTRUCTIVE PASS:",len(cases))
