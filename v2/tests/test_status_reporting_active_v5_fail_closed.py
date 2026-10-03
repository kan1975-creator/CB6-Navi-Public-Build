#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_active_v5.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v5 active baseline failed")
cases=[
 ("demote-active","v2/gates/status_reporting_contract_v5.json",lambda d:d.update({"status":"CANDIDATE"}),"active v5 identity/status invalid"),
 ("reset-start","v2/gates/status_reporting_contract_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"].update({"run_start_basis":"LATEST_CHECK"}),"immutable run start missing"),
 ("reset-intermediate","v2/gates/status_reporting_contract_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["later_wait"].update({"intermediate_check_must_not_reset_basis":False}),"later wait rule invalid"),
 ("restart-overdue","v2/gates/status_reporting_contract_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"restart_original_interval_forbidden":False}),"overdue wait rule invalid"),
 ("wait-after-complete","v2/gates/status_reporting_contract_v5.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["completed_run"].update({"report_completed_result_instead_of_wait":False}),"completed run rule invalid"),
 ("registry-old","v2/gates/operational_rule_registry_v8.json",lambda d:[x.update({"contract":"v2/gates/status_reporting_contract_v4.json"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"registry v8 active binding invalid"),
 ("coverage-old","v2/gates/rule_coverage.json",lambda d:d.update({"registry":"v2/gates/operational_rule_registry_v7.json"}),"machine coverage v8 missing")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v5-active rejection:",name)
print("PASS status reporting v5 active destructive cases rejected")
