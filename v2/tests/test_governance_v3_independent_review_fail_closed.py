#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_governance_v3_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("governance v3 review baseline failed")
cases=[
 ("break-lineage","v2/gates/operational_rule_registry_v3.json",lambda d:d.update({"supersedes":"wrong"}),"v3 lineage missing"),
 ("remove-contract","v2/gates/operational_rule_registry_v3.json",lambda d:[x.update({"contract":None}) for x in d["rules"] if x.get("id")=="OPS-USER-APPROVAL-BEFORE-FIX-001"],"approval contract binding missing"),
 ("allow-reuse","v2/gates/operational_rule_registry_v3.json",lambda d:[x["proposal"].update({"approval_reuse_for_different_change_forbidden":False}) for x in d["rules"] if x.get("id")=="OPS-USER-APPROVAL-BEFORE-FIX-001"],"approval fail-closed protections weakened"),
 ("pretend-freeze-changed","v2/gates/user_approval_rule_change_record.json",lambda d:d.update({"freeze_lock_unchanged":False}),"pre-adoption authority was modified")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d))
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected governance-v3-review rejection:",name)
print("PASS governance v3 independent-review destructive cases rejected")
