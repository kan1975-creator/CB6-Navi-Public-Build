#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_completion_gaps_e2e_independent_review.py"];F="v2/gates/development_auditor_v2_completion_gaps_e2e_cases.json"
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("independent review baseline failed")
def mutate(case,fn):
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/F;d=json.loads(p.read_text());c=next(x for x in d["cases"] if x["id"]==case);fn(c);p.write_text(json.dumps(d,indent=2)+"\\n")
  if run(r).returncode==0:raise SystemExit("independent destructive case passed:"+case)
  print("PASS expected independent rejection:",case)
mutate("CG-01",lambda c:c["evidence_check"].update({"exists":True}))
mutate("CG-02",lambda c:c["scope_check"].update({"purpose_matches":True}))
mutate("CG-03",lambda c:c["independent_review_check"].update({"reconstructed_from_raw_evidence":True,"reuses_candidate_conclusion":False,"reuses_candidate_intermediate_decision":False}))
mutate("CG-03",lambda c:c.update({"expected":"PASS"}))
print("AUDITOR V2 COMPLETION GAPS INDEPENDENT DESTRUCTIVE PASS: 4")
