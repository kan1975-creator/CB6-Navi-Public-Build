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
("drop-incident-e2e-candidate-evidence","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"].pop("incident_e2e_candidate")),
("falsify-incident-e2e-review","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["incident_e2e_independent_review"].update({"conclusion":"failure"})),
("drop-stage-forgetting-e2e-candidate-evidence","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"].pop("stage_forgetting_e2e_candidate")),
("falsify-stage-forgetting-e2e-review","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["stage_forgetting_e2e_independent_review"].update({"conclusion":"failure"})),
("drop-remaining-gaps-e2e-candidate-evidence","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"].pop("remaining_gaps_e2e_candidate")),
("falsify-remaining-gaps-e2e-review","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["remaining_gaps_e2e_independent_review"].update({"conclusion":"failure"})),
("drop-final-red-team-e2e-candidate-evidence","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"].pop("final_red_team_e2e_candidate")),
("falsify-final-red-team-e2e-review","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["final_red_team_e2e_independent_review"].update({"conclusion":"failure"})),
("drop-completion-gaps-e2e-candidate-evidence","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"].pop("completion_gaps_e2e_candidate")),
("falsify-completion-gaps-e2e-review","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["completion_gaps_e2e_independent_review"].update({"conclusion":"failure"})),
("falsify-completion-gaps-e2e-candidate-head","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["completion_gaps_e2e_candidate"].update({"candidate_head":"STALE"})),
("falsify-completion-gaps-e2e-review-head","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["completion_gaps_e2e_independent_review"].update({"candidate_head":"STALE"})),
("drop-final-e2e-branch-coverage","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"].pop("final_e2e_branch_coverage")),
("falsify-final-e2e-development-gate","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["final_e2e_branch_coverage"]["development_gate"].update({"run_id":0})),
("drop-atomic-coverage-evidence","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"].pop("atomic_coverage_e2e")),
("falsify-atomic-candidate","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["atomic_coverage_e2e"]["candidate"].update({"conclusion":"failure"})),
("falsify-atomic-independent-review","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["atomic_coverage_e2e"]["independent_review"].update({"run_id":0})),
("falsify-atomic-development-gate","v2/gates/development_auditor_adoption_evidence_v2.json",lambda d:d["evidence"]["atomic_coverage_e2e"]["development_gate"].update({"conclusion":"failure"})),
("stale-postchange-head","v2/gates/development_auditor_postchange_certification_v2.json",lambda d:d.update({"postchange_head":"STALE"})),
("falsify-postchange-development-gate","v2/gates/development_auditor_postchange_certification_v2.json",lambda d:d["development_gate"].update({"conclusion":"failure"})),
("falsify-postchange-atomic-candidate","v2/gates/development_auditor_postchange_certification_v2.json",lambda d:d["atomic_coverage"]["candidate"].update({"run_id":0})),
("falsify-postchange-independent-review","v2/gates/development_auditor_postchange_certification_v2.json",lambda d:d["atomic_coverage"]["independent_review"].update({"conclusion":"failure"})),
("weaken-postchange-root-certification","v2/gates/development_auditor_postchange_certification_v2.json",lambda d:d["root_certification"].update({"status":"UNPROVEN"})),
("weaken-postchange-method-freeze","v2/gates/development_auditor_postchange_certification_v2.json",lambda d:d["method_freeze"].update({"result":"FAIL"})),
("drop-v2-coverage","v2/gates/rule_coverage.json",lambda d:d["entries"].__setitem__(len(d["entries"])-1,{"rule_id":"CB6-DEVELOPMENT-AUDITOR-V2","coverage_status":"PROPOSED"}))
]
for name,file,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/file;d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\\n")
  if run(r).returncode==0:raise SystemExit("V2 active destructive case passed:"+name)
  print("PASS expected V2 ACTIVE rejection:",name)
print("CB6 DEVELOPMENT AUDITOR V2 ACTIVE DESTRUCTIVE PASS:",len(cases))
