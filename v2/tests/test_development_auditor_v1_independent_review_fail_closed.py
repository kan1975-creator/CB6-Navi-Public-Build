#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_development_auditor_v1_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("auditor independent baseline failed")
cases=[
 ("allow-stale-head",lambda d:d["freshness"].update({"head_change_requires_resynchronization":False}),"auditor freshness invalid"),
 ("drop-research",lambda d:d["audit_dimensions"].remove("multidirectional_research"),"audit dimension missing"),
 ("reuse-future-approval",lambda d:d["approval_boundary"].update({"unknown_future_change_may_reuse_prior_approval":True}),"approval boundary invalid"),
 ("allow-app-change",lambda d:d["non_interference"].update({"application_source_change_forbidden":False}),"non-interference invalid"),
]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/development_auditor_candidate_v1.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected auditor independent rejection:",name)
print("PASS auditor independent destructive cases rejected")
