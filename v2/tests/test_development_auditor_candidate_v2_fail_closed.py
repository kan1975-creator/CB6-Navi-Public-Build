#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_development_auditor_candidate_v2.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("baseline failed")
cases=[]
def add(name,file,fn):cases.append((name,file,fn))
add("drop-ac18","v2/gates/development_auditor_candidate_v2.json",lambda d:d["acceptance_criteria"].pop())
add("mandatory-na","v2/gates/development_auditor_candidate_v2.json",lambda d:d["applicability"].update({"mandatory_not_applicable_forbidden":False}))
add("zero-result-allowed","v2/gates/development_auditor_candidate_v2.json",lambda d:d["evidence_sufficiency"].update({"negative_conclusion_from_single_zero_result_forbidden":False}))
add("drop-countercheck","v2/gates/development_auditor_candidate_v2.json",lambda d:d["evidence_sufficiency"].update({"negative_conclusion_requires_independent_authoritative_countercheck_or_completeness_proof":False}))
add("wrong-head-allowed","v2/gates/development_auditor_candidate_v2.json",lambda d:d["evidence_sufficiency"].update({"wrong_head_evidence_forbidden":False}))
add("reuse-work-unit","v2/gates/development_auditor_candidate_v2.json",lambda d:d["evidence_sufficiency"].update({"cross_work_unit_evidence_reuse_without_explicit_binding_forbidden":False}))
add("drop-alternative","v2/gates/development_auditor_candidate_v2.json",lambda d:d["semantic_audit"].update({"requires_counter_hypothesis_or_alternative_for_material_decisions":False}))
add("implement-before-approval","v2/gates/development_auditor_candidate_v2.json",lambda d:d["work_unit"].update({"implementation_before_approval_bound_forbidden":False}))
add("scope-drift","v2/gates/development_auditor_candidate_v2.json",lambda d:d["approval"].update({"scope_expansion_requires_new_bound_approval":False}))
add("low-risk-escape","v2/gates/development_auditor_candidate_v2.json",lambda d:d["risk"].update({"self_declared_low_cannot_reduce_mandatory_checks":False}))
add("drop-independent-review","v2/gates/development_auditor_candidate_v2.json",lambda d:d["independent_review"].update({"required_before_pass":False}))
add("allow-disagreement-pass","v2/gates/development_auditor_candidate_v2.json",lambda d:d["independent_review"].update({"blocking_disagreement_forbids_pass":False}))
add("allow-diff-drift","v2/gates/development_auditor_candidate_v2.json",lambda d:d["exit_audit"].update({"actual_diff_must_match_declared_scope":False}))
add("allow-app-change","v2/gates/development_auditor_candidate_v2.json",lambda d:d["non_interference"].update({"application_source_change_forbidden":False}))
add("allow-development-gate-change","v2/gates/development_auditor_candidate_v2.json",lambda d:d["non_interference"].update({"development_gate_change_forbidden_in_candidate_stage":False}))
add("self-activate","v2/gates/development_auditor_candidate_v2.json",lambda d:d.update({"status":"ACTIVE"}))
add("schema-zero-result","v2/gates/development_auditor_work_unit_schema_v1.json",lambda d:d["negative_conclusion"].update({"single_zero_result_insufficient":False}))
for name,file,fn in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/file;d=json.loads(p.read_text());fn(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  cp=run(r)
  if cp.returncode==0:raise SystemExit("destructive case unexpectedly passed:"+name)
  print("PASS expected rejection:",name)
print("CB6 DEVELOPMENT AUDITOR V2 CANDIDATE DESTRUCTIVE PASS:",len(cases))
