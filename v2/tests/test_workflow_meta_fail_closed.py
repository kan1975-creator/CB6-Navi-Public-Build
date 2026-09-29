#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def run(name,mut,needle):
 with tempfile.TemporaryDirectory() as d:
  x=Path(d)/"r";shutil.copytree(R,x);p=x/".github/workflows/cb6_development_gate.yml";s=p.read_text();p.write_text(mut(s))
  q=subprocess.run(["python3",str(x/"v2/gates/verify_workflow_meta.py")],cwd=x,text=True,capture_output=True);o=q.stdout+q.stderr
  if q.returncode==0 or needle not in o:raise SystemExit(name+" did not fail correctly\n"+o)
  print("PASS expected workflow-meta rejection:",name);print(" ",[z for z in o.splitlines() if needle in z][0])
target="python3 v2/gates/verify_rule_coverage.py"
run("required-verifier-zero",lambda s:s.replace(target,"echo omitted"),"workflow invocation count=0")
run("required-verifier-duplicate",lambda s:s.replace(target,target+"\n        run: "+target),"workflow invocation count=2")
print("PASS workflow meta destructive cases rejected")
