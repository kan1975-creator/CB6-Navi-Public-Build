#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v3 independent review baseline failed")
cases=[
 ("direct-active","v2/gates/status_reporting_contract_v3.json",lambda d:d["activation"].update({"direct_active_forbidden":False}),"candidate allows direct activation"),
 ("drop-fourth-line","v2/gates/status_reporting_contract_v3.json",lambda d:d["required_report_fields"].remove("スマホ操作"),"four-line fields invalid"),
 ("wrong-four-line-form","v2/gates/status_reporting_contract_v3.json",lambda d:d["four_line_template"]["no_user_operation_form"].update({"ChatGPTアプリ":"開いたまま"}),"four-line template invalid"),
 ("active-v2-demoted","v2/gates/status_reporting_contract_v2.json",lambda d:d.update({"status":"CANDIDATE"}),"ACTIVE v2 authority changed"),
 ("registry-rebound","v2/gates/operational_rule_registry_v5.json",lambda d:[x.update({"contract":"v2/gates/status_reporting_contract_v3.json"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"ACTIVE registry binding changed")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text(encoding="utf-8")); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v3-review rejection:",name)
print("PASS status reporting v3 independent-review destructive cases rejected")
