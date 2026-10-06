#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_development_auditor_v2_incident_e2e.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("baseline failed")
cases=[
("approval-bypass",0,lambda c:c.update({"approval_bound_before_implementation":True})),
("scope-drift-bypass",1,lambda c:c.update({"actual_diff_within_approved_scope":True})),
("source-first-bypass",2,lambda c:c.update({"source_first_research_complete":True})),
("impact-bypass",3,lambda c:c.update({"impact_complete":True})),
("prior-failure-bypass",4,lambda c:c.update({"prior_failure_complete":True})),
("zero-result-bypass",5,lambda c:c.update({"negative_conclusion_sufficient":True})),
("stale-head-bypass",6,lambda c:c.update({"head_current":True})),
("valid-work-unit-false-stop",7,lambda c:c.update({"head_current":False}))
]
for name,idx,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/development_auditor_v2_incident_e2e_cases.json"; d=json.loads(p.read_text()); mut(d["cases"][idx]); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0: raise SystemExit("destructive case unexpectedly passed:"+name)
  print("PASS expected E2E rejection:",name)
print("AUDITOR V2 INCIDENT E2E DESTRUCTIVE PASS:",len(cases))
