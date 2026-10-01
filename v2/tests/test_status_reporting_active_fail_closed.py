#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_status_reporting_active.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("status reporting active baseline failed")
cases=[
 ("demote-active","v2/gates/status_reporting_contract_v1.json",lambda d:d.update({"status":"CANDIDATE"}),"active identity/status invalid"),
 ("drop-japanese-tag","v2/gates/status_reporting_contract_v1.json",lambda d:d["report_tags"].update({"allowed":["ガバナンス","信号機","コンビニ"]}),"report tags invalid"),
 ("drop-future","v2/gates/status_reporting_contract_v1.json",lambda d:d["scope"].update({"applies_to_unknown_future_features_without_enumeration":False}),"scope weakened"),
 ("registry-proposed","v2/gates/operational_rule_registry_v4.json",lambda d:[x.update({"status":"PROPOSED"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"registry active binding invalid"),
 ("coverage-missing","v2/gates/rule_coverage.json",lambda d:d.update({"entries":[x for x in d["entries"] if x.get("rule_id")!="OPS-STATUS-REPORTING-001"]}),"machine coverage missing"),
 ("adoption-run-wrong","v2/gates/status_reporting_contract_v1.json",lambda d:d["adoption"].update({"independent_review_run_id":0}),"adoption evidence invalid")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path;d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r);out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out:raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-active rejection:",name)
print("PASS status reporting active destructive cases rejected")
