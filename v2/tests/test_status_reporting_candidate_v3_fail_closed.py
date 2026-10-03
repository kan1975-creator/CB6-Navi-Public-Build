#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v3.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("status reporting v3 candidate baseline failed")
cases=[
 ("drop-field",lambda d:d["required_report_fields"].remove("ChatGPTアプリ"),"four-line required fields invalid"),
 ("wrong-next-action",lambda d:d["four_line_template"]["no_user_operation_form"].update({"次にユーザーがすること":"待機"}),"canonical no-user-operation form invalid"),
 ("wrong-app-state",lambda d:d["four_line_template"]["no_user_operation_form"].update({"ChatGPTアプリ":"開いたまま"}),"canonical no-user-operation form invalid"),
 ("wrong-smartphone-state",lambda d:d["four_line_template"]["no_user_operation_form"].update({"スマホ操作":"不要"}),"canonical no-user-operation form invalid"),
 ("demote-v2",None,"ACTIVE v2 was not preserved")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_v3.json";d=json.loads(p.read_text())
  if mut: mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  else:
   q=r/"v2/gates/status_reporting_contract_v2.json";a=json.loads(q.read_text());a["status"]="CANDIDATE";q.write_text(json.dumps(a,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r);out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out:raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v3 rejection:",name)
print("PASS status reporting v3 candidate destructive cases rejected")
