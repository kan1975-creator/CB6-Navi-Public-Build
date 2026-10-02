#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_status_reporting_active_v2.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("status reporting v2 active baseline failed")
cases=[
 ("drop-post-wait","v2/gates/status_reporting_contract_v2.json",lambda d:d["rules"]["待ち"]["post_wait_user_instruction"].update({"required":False}),"post-wait instruction invalid"),
 ("demote-active","v2/gates/status_reporting_contract_v2.json",lambda d:d.update({"status":"CANDIDATE"}),"active v2 identity/status invalid"),
 ("registry-old-contract","v2/gates/operational_rule_registry_v5.json",lambda d:[x.update({"contract":"v2/gates/status_reporting_contract_v1.json"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"registry v5 active binding invalid"),
 ("coverage-old-registry","v2/gates/rule_coverage.json",lambda d:d.update({"registry":"v2/gates/operational_rule_registry_v4.json"}),"machine coverage v5 missing")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path;d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r);out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out:raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v2-active rejection:",name)
print("PASS status reporting v2 active destructive cases rejected")
