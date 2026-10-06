#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_active_v2.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("V2 active baseline failed")
cases=[
("allow-zero-result", "v2/gates/development_auditor_candidate_v2.json",lambda d:d["evidence_sufficiency"].update({"negative_conclusion_from_single_zero_result_forbidden":False})),
("allow-scope-drift","v2/gates/development_auditor_candidate_v2.json",lambda d:d["approval"].update({"scope_expansion_requires_new_bound_approval":False})),
("allow-disagreement","v2/gates/development_auditor_candidate_v2.json",lambda d:d["independent_review"].update({"blocking_disagreement_forbids_pass":False})),
("remove-adoption","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d.update({"status":"PROPOSED"})),
("drop-v2-coverage","v2/gates/rule_coverage.json",lambda d:d["entries"].__setitem__(len(d["entries"])-1,{"rule_id":"CB6-DEVELOPMENT-AUDITOR-V2","coverage_status":"PROPOSED"}))
]
for name,file,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/file;d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("V2 active destructive case passed:"+name)
  print("PASS expected V2 ACTIVE rejection:",name)
print("CB6 DEVELOPMENT AUDITOR V2 ACTIVE DESTRUCTIVE PASS:",len(cases))
