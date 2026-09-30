#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_governance_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("governance review baseline failed")
cases=[
 ("erase-reason","v2/gates/operational_rule_registry_v2.json",lambda d:d.update({"change_reason":""}),"change reason missing"),
 ("pretend-active-changed","v2/gates/rule_adoption_change_record.json",lambda d:d.update({"active_registry_unchanged":False}),"pre-adoption authority was modified"),
 ("allow-self-adoption","v2/gates/method_revision_procedure_v1.json",lambda d:d["invariants"].update({"candidate_cannot_verify_its_own_adoption":False}),"self-adoption protection missing")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d))
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected governance-review rejection:",name)
print("PASS governance independent-review destructive cases rejected")
