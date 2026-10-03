#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v5.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v5 candidate baseline failed")
cases=[
 ("reset-run-start",lambda d:d["rules"]["待ち"]["wait_time_display"].update({"run_start_basis":"LATEST_CHECK"}),"immutable run start missing"),
 ("omit-first-jst",lambda d:d["rules"]["待ち"]["wait_time_display"]["first_wait"].update({"show_run_start_time_jst":False}),"first wait rule invalid"),
 ("reset-on-intermediate",lambda d:d["rules"]["待ち"]["wait_time_display"]["later_wait"].update({"intermediate_check_must_not_reset_basis":False}),"later wait rule invalid"),
 ("omit-cumulative",lambda d:d["rules"]["待ち"]["wait_time_display"]["later_wait"].update({"show_cumulative_elapsed_from_original_run_start":False}),"later wait rule invalid"),
 ("restart-interval",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"restart_original_interval_forbidden":False}),"overdue wait rule invalid"),
 ("wait-after-complete",lambda d:d["rules"]["待ち"]["wait_time_display"]["completed_run"].update({"report_completed_result_instead_of_wait":False}),"completed run rule invalid"),
 ("distort-history",lambda d:d["rules"]["待ち"]["wait_time_display"]["history"].update({"user_check_delay_must_not_distort_duration":False}),"wait history rule invalid")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_candidate_v5.json"; q=json.loads(p.read_text()); mut(q); p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v5 rejection:",name)
print("PASS status reporting v5 wait-time destructive cases rejected")
