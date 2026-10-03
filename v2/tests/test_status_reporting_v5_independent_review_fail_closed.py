#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_v5_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v5 independent review baseline failed")
cases=[
 ("reset-run-start","v2/gates/status_reporting_contract_candidate_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"].update({"run_start_basis":"LATEST_CHECK"}),"immutable run start missing"),
 ("reset-intermediate","v2/gates/status_reporting_contract_candidate_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["later_wait"].update({"intermediate_check_must_not_reset_basis":False}),"later wait rule invalid"),
 ("restart-overdue","v2/gates/status_reporting_contract_candidate_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"restart_original_interval_forbidden":False}),"overdue wait rule invalid"),
 ("wait-after-complete","v2/gates/status_reporting_contract_candidate_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["completed_run"].update({"report_completed_result_instead_of_wait":False}),"completed run rule invalid"),
 ("self-active","v2/gates/status_reporting_contract_candidate_v5.json",lambda d:(d.update({"status":"ACTIVE"}),d["adoption"].update({"status":"ADOPTED"})),"v5 candidate identity/status invalid"),
 ("active-v4-demoted","v2/gates/status_reporting_contract_v4.json",lambda d:d.update({"status":"CANDIDATE"}),"ACTIVE v4 authority changed")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text(encoding="utf-8")); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v5-review rejection:",name)
print("PASS status reporting v5 independent-review destructive cases rejected")
