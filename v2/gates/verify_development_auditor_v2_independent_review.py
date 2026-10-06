#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
c=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
v1=json.loads((R/"v2/gates/development_auditor_candidate_v1.json").read_text())
reg=json.loads((R/"v2/gates/operational_rule_registry_v17.json").read_text())
if c.get("id")!="CB6-DEVELOPMENT-AUDITOR-V1" or c.get("revision")!=2 or c.get("status")!="CANDIDATE":e.append("V2 candidate identity")
if v1.get("status")!="CANDIDATE":e.append("V1 candidate basis changed")
rules={x.get("id"):x for x in reg.get("rules",[])}
if rules.get("CB6-DEVELOPMENT-AUDITOR-V1",{}).get("status")!="ACTIVE":e.append("ACTIVE V1 authority not preserved")
for n in range(1,19):
 if not any(x.startswith(f"AC-{n:02d} ") for x in c.get("acceptance_criteria",[])):e.append(f"AC-{n:02d} absent")
a=c.get("applicability",{})
if a.get("mandatory_not_applicable_forbidden") is not True or a.get("conditional_not_applicable_requires_reason_and_evidence") is not True:e.append("N/A semantic boundary")
ev=c.get("evidence_sufficiency",{})
if ev.get("negative_conclusion_from_single_zero_result_forbidden") is not True or ev.get("negative_conclusion_requires_independent_authoritative_countercheck_or_completeness_proof") is not True:e.append("negative conclusion evidence insufficient")
sem=c.get("semantic_audit",{})
if sem.get("requires_finding") is not True or sem.get("requires_counter_hypothesis_or_alternative_for_material_decisions") is not True or sem.get("requires_unresolved_items") is not True:e.append("semantic challenge incomplete")
ap=c.get("approval",{})
if ap.get("scope_expansion_requires_new_bound_approval") is not True or not {"change_id","basis_head","purpose","affected_domains","planned_paths","forbidden_scope"}.issubset(set(ap.get("binding_fields",[]))):e.append("approval semantic binding")
ex=c.get("exit_audit",{})
if ex.get("actual_diff_must_match_declared_scope") is not True or ex.get("approval_mismatch_forbids_pass") is not True or ex.get("blocked_or_unresolved_blocker_forbids_pass") is not True:e.append("exit semantic scope")
ir=c.get("independent_review",{})
if ir.get("must_reconstruct_from_target_head_work_unit_active_authority_and_raw_evidence") is not True:e.append("review does not independently reconstruct")
if ir.get("implementation_success_claims_are_not_review_evidence") is not True:e.append("implementation conclusion may substitute for evidence")
if ir.get("blocking_disagreement_forbids_pass") is not True:e.append("blocking disagreement escape")
if s.get("negative_conclusion",{}).get("single_zero_result_insufficient") is not True:e.append("work-unit zero-result escape")
pr=s.get("pass_requires",{})
for k in ("basis_target_head_current","mandatory_dimensions_applied","no_blocked_dimension","no_unresolved_blocker","approval_bound_before_implementation","actual_diff_within_approved_scope","validation_complete","independent_review_accepted","no_blocking_disagreement"):
 if pr.get(k) is not True:e.append("PASS semantic prerequisite:"+k)
ni=c.get("non_interference",{})
for k in ("application_source_change_forbidden","active_v1_change_forbidden_in_candidate_stage","registry_coverage_change_forbidden_in_candidate_stage","method_freeze_change_forbidden_in_candidate_stage","development_gate_change_forbidden_in_candidate_stage"):
 if ni.get(k) is not True:e.append("review non-interference:"+k)
if c.get("activation",{}).get("self_activation_forbidden") is not True:e.append("self activation")
if e:
 print("CB6 DEVELOPMENT AUDITOR V2 INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT AUDITOR V2 INDEPENDENT REVIEW PASS: raw-evidence reconstruction, semantic challenge, approval/diff scope, disagreement and non-interference independently preserved")
