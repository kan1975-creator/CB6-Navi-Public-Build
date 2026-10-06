#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def check(root,needle):
 q=subprocess.run(["python3",str(root/"v2/gates/verify_workflow_meta.py")],cwd=root,text=True,capture_output=True);o=q.stdout+q.stderr
 if q.returncode==0 or needle not in o: raise SystemExit("did not fail correctly\n"+o)
 print("PASS expected workflow-meta rejection:",needle)
with tempfile.TemporaryDirectory() as d:
 x=Path(d)/"r";shutil.copytree(R,x);p=x/".github/workflows/cb6_development_gate.yml";s=p.read_text();p.write_text(s.replace("python3 v2/gates/verify_rule_coverage.py","echo omitted"));check(x,"workflow invocation count=0")
with tempfile.TemporaryDirectory() as d:
 x=Path(d)/"r";shutil.copytree(R,x);p=x/".github/workflows/cb6_development_gate.yml";s=p.read_text();t="python3 v2/gates/verify_rule_coverage.py";p.write_text(s.replace(t,t+"\n        run: "+t));check(x,"workflow invocation count=2")
with tempfile.TemporaryDirectory() as d:
 x=Path(d)/"r";shutil.copytree(R,x);(x/".github/workflows/cb6_hourly_development_cycle.yml").unlink();check(x,"hourly development workflow missing")
with tempfile.TemporaryDirectory() as d:
 x=Path(d)/"r";shutil.copytree(R,x);p=x/".github/workflows/cb6_hourly_development_cycle.yml";s=p.read_text();p.write_text(s.replace("17 * * * *","17 18 * * *"));check(x,"lacks hourly schedule")
for label,rel,old,new,needle in [
 ("pr",".github/workflows/cb6_development_gate.yml","pull_request:","pull_request_REMOVED:","Development Gate lacks pull_request reachability"),
 ("manual",".github/workflows/cb6_development_gate.yml","workflow_dispatch:","workflow_dispatch_REMOVED:","Development Gate lacks workflow_dispatch reachability"),
 ("feature-auditor","v2/gates/verify_project_gate.py","verify_development_auditor_active_v2.py","verify_development_auditor_active_v2_REMOVED.py","feature gate lacks Auditor V2 runtime blocking")]:
 with tempfile.TemporaryDirectory() as d:
  x=Path(d)/"r";shutil.copytree(R,x);p=x/rel;s=p.read_text();p.write_text(s.replace(old,new,1));check(x,needle)
print("PASS workflow meta destructive cases rejected")
