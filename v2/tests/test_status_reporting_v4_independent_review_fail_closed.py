#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_v4_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v4 independent review baseline failed")
cases=[
 ("direct-active","v2/gates/status_reporting_contract_candidate_v4.json",lambda d:d["activation"].update({"direct_active_forbidden":False}),"candidate allows direct activation"),
 ("not-final-four","v2/gates/status_reporting_contract_candidate_v4.json",lambda d:d["four_line_template"].update({"placement":"ANYWHERE"}),"final four-line placement invalid"),
 ("reordered-four","v2/gates/status_reporting_contract_candidate_v4.json",lambda d:d["four_line_template"].update({"order_exactly_required":["分類","ChatGPTアプリ","次にユーザーがすること","スマホ操作"]}),"final four-line placement invalid"),
 ("allow-after-four","v2/gates/status_reporting_contract_candidate_v4.json",lambda d:d["four_line_template"].update({"content_after_four_lines_forbidden":False}),"final four-line placement invalid"),
 ("allow-unidentified","v2/gates/status_reporting_contract_candidate_v4.json",lambda d:d["rules"]["スマホ操作が必要"]["fail_closed"].update({"if_concrete_operation_not_identified":"ALLOW"}),"smartphone fail-closed invalid"),
 ("active-v3-demoted","v2/gates/status_reporting_contract_v3.json",lambda d:d.update({"status":"CANDIDATE"}),"ACTIVE v3 authority changed"),
 ("registry-rebound","v2/gates/operational_rule_registry_v6.json",lambda d:[x.update({"contract":"v2/gates/status_reporting_contract_candidate_v4.json"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"ACTIVE registry v6 binding changed")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text(encoding="utf-8")); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v4-review rejection:",name)
print("PASS status reporting v4 independent-review destructive cases rejected")
