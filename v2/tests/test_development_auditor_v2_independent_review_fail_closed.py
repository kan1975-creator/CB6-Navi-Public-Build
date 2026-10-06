#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_independent_review.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("independent baseline failed")
cases=[
("empty-semantic-challenge",lambda d:d["semantic_audit"].update({"requires_counter_hypothesis_or_alternative_for_material_decisions":False})),
("implementation-claim-as-evidence",lambda d:d["independent_review"].update({"implementation_success_claims_are_not_review_evidence":False})),
("no-raw-reconstruction",lambda d:d["independent_review"].update({"must_reconstruct_from_target_head_work_unit_active_authority_and_raw_evidence":False})),
("disagreement-pass",lambda d:d["independent_review"].update({"blocking_disagreement_forbids_pass":False})),
("approval-head-unbound",lambda d:d["approval"]["binding_fields"].remove("basis_head")),
("approval-domain-unbound",lambda d:d["approval"]["binding_fields"].remove("affected_domains")),
("actual-diff-unchecked",lambda d:d["exit_audit"].update({"actual_diff_must_match_declared_scope":False})),
("unresolved-pass",lambda d:d["exit_audit"].update({"blocked_or_unresolved_blocker_forbids_pass":False})),
("zero-search-as-proof",lambda d:d["evidence_sufficiency"].update({"negative_conclusion_from_single_zero_result_forbidden":False})),
("zero-search-no-countercheck",lambda d:d["evidence_sufficiency"].update({"negative_conclusion_requires_independent_authoritative_countercheck_or_completeness_proof":False})),
("mandatory-na",lambda d:d["applicability"].update({"mandatory_not_applicable_forbidden":False})),
("allow-app-change",lambda d:d["non_interference"].update({"application_source_change_forbidden":False})),
("self-activate",lambda d:d["activation"].update({"self_activation_forbidden":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/development_auditor_candidate_v2.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("semantic bypass passed:"+name)
  print("PASS expected independent rejection:",name)
print("CB6 DEVELOPMENT AUDITOR V2 INDEPENDENT DESTRUCTIVE PASS:",len(cases))
