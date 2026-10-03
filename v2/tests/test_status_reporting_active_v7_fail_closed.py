#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_active_v7.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v7 active baseline failed")
cases=[
 ("demote","v2/gates/status_reporting_contract_v7.json",lambda d:d.update({"status":"CANDIDATE"}),"active v7 identity/status invalid"),
 ("fixed-threshold","v2/gates/status_reporting_contract_v7.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"fixed_or_unsubstantiated_threshold_forbidden":False}),"normal duration guard invalid"),
 ("wrong-basis","v2/gates/status_reporting_contract_v7.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"basis":"FIXED_MINUTES"}),"normal duration evidence basis missing"),
 ("change-v6-display","v2/gates/status_reporting_contract_v7.json",lambda d:d["final_summary_display"].update({"duplicate_information_forbidden":False}),"existing ACTIVE v6 contract changed"),
 ("registry-old","v2/gates/operational_rule_registry_v10.json",lambda d:[x.update({"contract":"v2/gates/status_reporting_contract_v6.json"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"registry v10 active binding invalid"),
 ("coverage-old","v2/gates/rule_coverage.json",lambda d:d.update({"registry":"v2/gates/operational_rule_registry_v9.json"}),"machine coverage v10 missing")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v7-active rejection:",name)
print("PASS status reporting v7 active destructive cases rejected")
