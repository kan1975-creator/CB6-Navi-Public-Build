#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v6.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v6 candidate baseline failed")
cases=[
 ("no-bullets",lambda d:d["final_summary_display"].update({"markdown_bullet_and_bold_required":False}),"final summary display rule invalid"),
 ("allow-duplicate",lambda d:d["final_summary_display"].update({"duplicate_information_forbidden":False}),"final summary display rule invalid"),
 ("wrong-placement",lambda d:d["final_summary_display"].update({"placement":"REPORT_BODY"}),"final summary display rule invalid"),
 ("omit-wait-fields",lambda d:d["final_summary_display"].update({"wait_additional_fields":[]}),"wait final fields invalid"),
 ("change-wait-rule",lambda d:d["rules"]["待ち"]["wait_time_display"].update({"run_start_basis":"LATEST_CHECK"}),"existing v5 contract changed: rules"),
 ("self-activate",lambda d:d.update({"status":"ACTIVE"}),"candidate v6 identity/status invalid")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_candidate_v6.json"; q=json.loads(p.read_text()); mut(q); p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v6 rejection:",name)
print("PASS status reporting v6 display destructive cases rejected")
