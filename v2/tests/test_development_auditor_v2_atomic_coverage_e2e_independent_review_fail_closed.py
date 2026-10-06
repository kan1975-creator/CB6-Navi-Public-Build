#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_atomic_coverage_e2e_independent_review.py"];F="v2/gates/development_auditor_v2_atomic_coverage_e2e_cases.json"
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("independent atomic baseline failed")
mutations=[
("drop-ac",lambda r:(lambda p,d:(d["acceptance_criteria"].pop(),p.write_text(json.dumps(d,indent=2)+"\n")))(r/"v2/gates/development_auditor_candidate_v2.json",json.loads((r/"v2/gates/development_auditor_candidate_v2.json").read_text()))),
("drop-na-reason",lambda r:(lambda p,d:(d["not_applicable_required"].remove("reason"),p.write_text(json.dumps(d,indent=2)+"\n")))(r/"v2/gates/development_auditor_work_unit_schema_v1.json",json.loads((r/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text()))),
("drop-method-stage",lambda r:(lambda p,d:(d["feature_development_pipeline"].pop(),p.write_text(json.dumps(d,indent=2)+"\n")))(r/"v2/gates/development_method_contract.json",json.loads((r/"v2/gates/development_method_contract.json").read_text()))),
("drop-e2e",lambda r:(r/"v2/gates/development_auditor_v2_incident_e2e_cases.json").unlink()),
("falsify-final-evidence",lambda r:(lambda p,d:(d["evidence"]["final_e2e_branch_coverage"]["development_gate"].update({"run_id":0}),p.write_text(json.dumps(d,indent=2)+"\n")))(r/"v2/gates/development_auditor_adoption_evidence_v2.json",json.loads((r/"v2/gates/development_auditor_adoption_evidence_v2.json").read_text())))
]
for name,mut in mutations:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));mut(r)
  if run(r).returncode==0:raise SystemExit("independent atomic defect passed:"+name)
print("AUDITOR V2 ATOMIC COVERAGE INDEPENDENT DESTRUCTIVE PASS:",len(mutations))
