#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting independent review baseline failed")
cases=[
 ("direct-active","v2/gates/status_reporting_contract_candidate_v1.json",lambda d:d["activation"].update({"direct_active_forbidden":False}),"candidate allows direct activation"),
 ("drop-japanese-tag","v2/gates/status_reporting_contract_candidate_v1.json",lambda d:d["report_tags"].update({"allowed":["ガバナンス","信号機","コンビニ"]}),"Japanese report tag contract invalid"),
 ("pre-adopt-active","v2/gates/operational_rule_registry_v3.json",lambda d:[x.update({"status":"ACTIVE"}) for x in d["rules"] if x.get("id")=="OPS-STATUS-REPORTING-001"],"pre-adoption registry authority changed"),
 ("allow-self-adoption","v2/gates/status_reporting_method_revision_candidate.json",lambda d:d["invariants"].update({"candidate_cannot_self_adopt":False}),"method revision pre-adoption protection invalid")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text(encoding="utf-8")); mut(d); p.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-review rejection:",name)
print("PASS status reporting independent-review destructive cases rejected")
