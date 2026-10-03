#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_active_v6.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v6 active baseline failed")
cases=[
 ("demote-active","v2/gates/status_reporting_contract_v6.json",lambda d:d.update({"status":"CANDIDATE"}),"active v6 identity/status invalid"),
 ("no-bold","v2/gates/status_reporting_contract_v6.json",lambda d:d["final_summary_display"].update({"markdown_bullet_and_bold_required":False}),"v6 final summary display invalid"),
 ("allow-duplicate","v2/gates/status_reporting_contract_v6.json",lambda d:d["final_summary_display"].update({"duplicate_information_forbidden":False}),"v6 final summary display invalid"),
 ("omit-wait-fields","v2/gates/status_reporting_contract_v6.json",lambda d:d["final_summary_display"].update({"wait_additional_fields":[]}),"v6 wait final fields invalid"),
 ("change-wait","v2/gates/status_reporting_contract_v6.json",lambda d:d["rules"]["待ち"]["wait_time_display"].update({"run_start_basis":"LATEST_CHECK"}),"existing ACTIVE v5 contract changed: rules"),
 ("registry-old","v2/gates/operational_rule_registry_v9.json",lambda d:[x.update({"contract":"v2/gates/status_reporting_contract_v5.json"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"registry v9 active binding invalid"),
 ("coverage-old","v2/gates/rule_coverage.json",lambda d:d.update({"registry":"v2/gates/operational_rule_registry_v8.json"}),"machine coverage v9 missing")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v6-active rejection:",name)
print("PASS status reporting v6 active destructive cases rejected")
