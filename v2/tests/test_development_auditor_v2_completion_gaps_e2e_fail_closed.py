#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_completion_gaps_e2e.py"];F="v2/gates/development_auditor_v2_completion_gaps_e2e_cases.json"
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("baseline failed")
def heal(c):
 if c["id"].startswith("CG-02"):c["scope_check"].update({"purpose_matches":True,"affected_domains_match":True,"forbidden_scope_entered":False,"rename_delete_semantically_safe":True})
 elif c["id"].startswith("CG-03"):c["independent_review_check"].update({"reconstructed_from_target_head":True,"reconstructed_from_work_unit":True,"reconstructed_from_active_authority":True,"reconstructed_from_raw_evidence":True,"reuses_candidate_conclusion":False,"reuses_candidate_intermediate_decision":False})
 else:c["evidence_check"].update({"exists":True,"target_matches":True,"semantically_supports_finding":True})
ids=["CG-01A","CG-01B","CG-01C","CG-02A","CG-02B","CG-02C","CG-02D","CG-03A","CG-03B","CG-03C","CG-03D","CG-03E","CG-03F"]
for cid in ids:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/F;d=json.loads(p.read_text());heal(next(x for x in d["cases"] if x["id"]==cid));p.write_text(json.dumps(d,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("defect erasure passed:"+cid)
print("AUDITOR V2 COMPLETION GAPS E2E DESTRUCTIVE PASS: 13")
