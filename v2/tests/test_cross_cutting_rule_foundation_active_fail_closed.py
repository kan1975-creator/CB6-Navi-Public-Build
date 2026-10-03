#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_cross_cutting_rule_foundation_active.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("cross-cutting ACTIVE baseline failed")
def mutate(root,path,fn):
 p=root/path;d=json.loads(p.read_text());fn(d);p.write_text(json.dumps(d))
cases=[
 ("drop-v3-rule",lambda r:mutate(r,"v2/gates/operational_rule_registry_v4.json",lambda d:d["rules"].pop()),"v3 ACTIVE rules not preserved exactly"),
 ("drop-feature-inheritance",lambda r:mutate(r,"v2/gates/features/signals.json",lambda d:d.pop("inherits_cross_cutting_rules",None)),"feature inheritance missing"),
 ("weaken-scope",lambda r:mutate(r,"v2/gates/operational_rule_registry_v4.json",lambda d:d["cross_cutting_foundation"].__setitem__("scope","current_only")),"scope weakened")]
for n,fn,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));fn(r);cp=run(r);out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out:raise SystemExit(n+" not rejected correctly\n"+out)
  print("PASS expected cross-cutting ACTIVE rejection:",n)
print("PASS cross-cutting ACTIVE destructive cases rejected")
