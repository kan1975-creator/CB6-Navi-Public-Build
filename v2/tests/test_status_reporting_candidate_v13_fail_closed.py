#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_status_reporting_candidate_v13.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("v13 candidate baseline failed")
cases=[
 ("missing-cumulative",lambda d:d["wait_final_summary"].update({"exact_order_required":["分類","次回確認目安","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]})),
 ("wrong-order",lambda d:d["wait_final_summary"].update({"exact_order_required":["分類","次回確認目安","累積経過時間","次にユーザーがすること","ChatGPTアプリ","スマホ操作"]})),
 ("nonterminal",lambda d:d["wait_final_summary"].update({"must_be_response_end":False})),
 ("timing-weakened",lambda d:d["preservation"].update({"evidence_based_next_check_preserved":False})),
 ("direct-active",lambda d:d["activation"].update({"direct_active_forbidden":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/status_reporting_contract_candidate_v13.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("v13 candidate destructive bypass:"+name)
  print("PASS expected candidate rejection:",name)
print("CB6 STATUS REPORTING V13 CANDIDATE DESTRUCTIVE PASS:",len(cases))
