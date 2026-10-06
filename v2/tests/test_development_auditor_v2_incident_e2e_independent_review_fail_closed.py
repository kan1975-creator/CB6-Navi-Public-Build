#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_incident_e2e_independent_review.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("independent baseline failed")
cases=[
("lie-expected-pass",lambda d:d["cases"][0].update({"expected":"PASS"})),
("erase-approval-defect",lambda d:d["cases"][0].update({"approval_bound_before_implementation":True})),
("erase-scope-drift",lambda d:d["cases"][1].update({"actual_diff_within_approved_scope":True})),
("erase-source-first-defect",lambda d:d["cases"][2].update({"source_first_research_complete":True})),
("fake-incident-id",lambda d:d["cases"][4].update({"incident_id":"INC-NOT-REAL"})),
("erase-zero-result-defect",lambda d:d["cases"][5].update({"negative_conclusion_sufficient":True})),
("erase-stale-head",lambda d:d["cases"][6].update({"head_current":True})),
("false-stop-valid-case",lambda d:d["cases"][7].update({"expected":"STOP"})),
("break-valid-prerequisite",lambda d:d["cases"][7].update({"validation_complete":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/development_auditor_v2_incident_e2e_cases.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("independent destructive case passed:"+name)
  print("PASS expected independent rejection:",name)
print("AUDITOR V2 INCIDENT E2E INDEPENDENT DESTRUCTIVE PASS:",len(cases))
