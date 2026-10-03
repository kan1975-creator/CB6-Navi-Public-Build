#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_v6_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v6 independent review baseline failed")
cases=[
 ("no-bold","v2/gates/status_reporting_contract_candidate_v6.json",lambda d:d["final_summary_display"].update({"markdown_bullet_and_bold_required":False}),"v6 final summary display invalid"),
 ("allow-duplicate","v2/gates/status_reporting_contract_candidate_v6.json",lambda d:d["final_summary_display"].update({"duplicate_information_forbidden":False}),"v6 final summary display invalid"),
 ("wrong-placement","v2/gates/status_reporting_contract_candidate_v6.json",lambda d:d["final_summary_display"].update({"placement":"REPORT_BODY"}),"v6 final summary display invalid"),
 ("omit-wait-fields","v2/gates/status_reporting_contract_candidate_v6.json",lambda d:d["final_summary_display"].update({"wait_additional_fields":[]}),"v6 wait final fields invalid"),
 ("change-wait-timing","v2/gates/status_reporting_contract_candidate_v6.json",lambda d:d["rules"]["待ち"]["wait_time_display"].update({"run_start_basis":"LATEST_CHECK"}),"existing ACTIVE v5 contract changed in candidate: rules"),
 ("self-active","v2/gates/status_reporting_contract_candidate_v6.json",lambda d:(d.update({"status":"ACTIVE"}),d["adoption"].update({"status":"ADOPTED"})),"v6 candidate identity/status invalid"),
 ("active-v5-demoted","v2/gates/status_reporting_contract_v5.json",lambda d:d.update({"status":"CANDIDATE"}),"ACTIVE v5 authority changed")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text(encoding="utf-8")); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v6-review rejection:",name)
print("PASS status reporting v6 independent-review destructive cases rejected")
