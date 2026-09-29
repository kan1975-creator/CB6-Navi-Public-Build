#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
 fid="reviewtest"; p=r/f"v2/gates/independent_review/{fid}.json"; p.parent.mkdir(parents=True,exist_ok=True)
 base={"schema":1,"feature_id":fid,"target_commit":"a"*40,"checklist":"v2/governance/audit_checklist_v1.md","review_context":"separate independent session","implementation_context_shared":False,"result":"ACCEPTED","evidence":["independent audit report"]}
 p.write_text(json.dumps(base))
 cmd=["python3","v2/gates/verify_independent_review.py",fid]
 ok=subprocess.run(cmd,cwd=r,text=True,capture_output=True)
 if ok.returncode: raise SystemExit("baseline failed: "+ok.stdout+ok.stderr)
 for name,mut,needle in [
  ("shared-context",lambda d:d.update(implementation_context_shared=True),"not independent"),
  ("wrong-checklist",lambda d:d.update(checklist="other.md"),"wrong checklist"),
  ("not-accepted",lambda d:d.update(result="PENDING"),"not accepted"),
  ("no-evidence",lambda d:d.update(evidence=[]),"traceable evidence missing")]:
  d=dict(base); mut(d); p.write_text(json.dumps(d))
  cp=subprocess.run(cmd,cwd=r,text=True,capture_output=True); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected: "+out)
  print("PASS expected independent-review rejection:",name)
print("PASS independent review destructive cases rejected")
