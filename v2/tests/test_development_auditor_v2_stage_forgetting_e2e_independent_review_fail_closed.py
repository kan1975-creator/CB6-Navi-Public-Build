#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_stage_forgetting_e2e_independent_review.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("independent baseline failed")
cases=[
("lie-expected-pass",lambda d:d["cases"][0].update({"expected":"PASS"})),
("erase-authority-defect",lambda d:d["cases"][0].update({"active_authority_complete":True})),
("erase-false-not-applicable",lambda d:d["cases"][1].update({"mandatory_dimensions_applied":True})),
("erase-counter-hypothesis-defect",lambda d:d["cases"][2].update({"counter_hypothesis_complete":True})),
("erase-blocker",lambda d:d["cases"][3].update({"unresolved_blocker":False})),
("erase-validation-defect",lambda d:d["cases"][4].update({"validation_evidence_complete":True})),
("erase-disagreement",lambda d:d["cases"][5].update({"blocking_disagreement":False})),
("erase-exit-evidence-defect",lambda d:d["cases"][6].update({"exit_evidence_complete":True}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/development_auditor_v2_stage_forgetting_e2e_cases.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("independent destructive case passed:"+name)
  print("PASS expected independent rejection:",name)
print("AUDITOR V2 STAGE FORGETTING E2E INDEPENDENT DESTRUCTIVE PASS:",len(cases))
