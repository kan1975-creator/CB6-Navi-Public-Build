#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_development_auditor_v2_stage_forgetting_e2e.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("baseline failed")
cases=[
("authority-forgetting-bypass",0,lambda c:c.update({"active_authority_complete":True})),
("false-not-applicable-bypass",1,lambda c:c.update({"mandatory_dimensions_applied":True})),
("counter-hypothesis-bypass",2,lambda c:c.update({"counter_hypothesis_complete":True})),
("unresolved-blocker-bypass",3,lambda c:c.update({"unresolved_blocker":False})),
("validation-evidence-bypass",4,lambda c:c.update({"validation_evidence_complete":True})),
("blocking-disagreement-bypass",5,lambda c:c.update({"blocking_disagreement":False})),
("exit-evidence-bypass",6,lambda c:c.update({"exit_evidence_complete":True}))
]
for name,idx,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/development_auditor_v2_stage_forgetting_e2e_cases.json"; d=json.loads(p.read_text()); mut(d["cases"][idx]); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0: raise SystemExit("destructive case unexpectedly passed:"+name)
  print("PASS expected stage-forgetting rejection:",name)
print("AUDITOR V2 STAGE FORGETTING E2E DESTRUCTIVE PASS:",len(cases))
