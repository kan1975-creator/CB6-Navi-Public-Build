#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; E=[]
old=json.loads((R/"v2/gates/development_auditor_candidate_v1.json").read_text())
c=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
s=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
if old.get("status")!="CANDIDATE": E.append("V1 candidate basis changed")
if c.get("id")!="CB6-DEVELOPMENT-AUDITOR-V1" or c.get("revision")!=2 or c.get("status")!="CANDIDATE": E.append("candidate identity")
if c.get("extends")!="v2/gates/development_auditor_candidate_v1.json": E.append("extension binding")
acs=set(c.get("acceptance_criteria",[]))
for n in range(1,19):
 if not any(x.startswith(f"AC-{n:02d} ") for x in acs): E.append(f"missing AC-{n:02d}")
mandatory={"freshness","active_authority","user_intent","applicable_rules_and_method","approval_boundary","change_impact","known_failures","actual_scope","unresolved_blockers"}
if not mandatory.issubset(set(c.get("mandatory_dimensions",[]))): E.append("mandatory dimensions incomplete")
a=c.get("applicability",{})
if a.get("states")!=["APPLIED","NOT_APPLICABLE","BLOCKED"] or a.get("mandatory_not_applicable_forbidden") is not True or a.get("conditional_not_applicable_requires_reason_and_evidence") is not True:E.append("applicability fail-closed")
ev=c.get("evidence_sufficiency",{})
for k in ("concrete_evidence_refs_required","negative_conclusion_from_single_zero_result_forbidden","negative_conclusion_requires_independent_authoritative_countercheck_or_completeness_proof","wrong_head_evidence_forbidden","cross_work_unit_evidence_reuse_without_explicit_binding_forbidden"):
 if ev.get(k) is not True:E.append("evidence sufficiency:"+k)
sem=c.get("semantic_audit",{})
for k in ("requires_finding","requires_counter_hypothesis_or_alternative_for_material_decisions","requires_impact_scope","requires_unresolved_items"):
 if sem.get(k) is not True:E.append("semantic audit:"+k)
w=c.get("work_unit",{})
if w.get("schema")!="v2/gates/development_auditor_work_unit_schema_v1.json":E.append("work unit schema binding")
if w.get("implementation_before_approval_bound_forbidden") is not True or w.get("head_change_requires_resynchronization") is not True:E.append("work unit transition guard")
ap=c.get("approval",{})
if ap.get("rule_id")!="OPS-USER-APPROVAL-BEFORE-FIX-001" or ap.get("scope_expansion_requires_new_bound_approval") is not True or ap.get("post_hoc_approval_forbidden") is not True:E.append("approval binding")
for x in ("change_id","basis_head","purpose","affected_domains","planned_paths","forbidden_scope"):
 if x not in ap.get("binding_fields",[]):E.append("approval field:"+x)
if c.get("risk",{}).get("self_declared_low_cannot_reduce_mandatory_checks") is not True:E.append("LOW risk escape")
ir=c.get("independent_review",{})
for k in ("required_before_pass","must_reconstruct_from_target_head_work_unit_active_authority_and_raw_evidence","implementation_success_claims_are_not_review_evidence","blocking_disagreement_forbids_pass"):
 if ir.get(k) is not True:E.append("independent review:"+k)
ex=c.get("exit_audit",{})
for k in ("actual_diff_must_match_declared_scope","missing_evidence_forbids_pass","stale_head_forbids_pass","approval_mismatch_forbids_pass","blocked_or_unresolved_blocker_forbids_pass"):
 if ex.get(k) is not True:E.append("exit audit:"+k)
ni=c.get("non_interference",{})
for k in ("application_source_change_forbidden","signal_behavior_change_forbidden","convenience_behavior_change_forbidden","search_routing_renderer_change_forbidden","existing_independent_review_weaken_forbidden","existing_gate_or_evidence_weaken_forbidden","active_v1_change_forbidden_in_candidate_stage","registry_coverage_change_forbidden_in_candidate_stage","method_freeze_change_forbidden_in_candidate_stage","development_gate_change_forbidden_in_candidate_stage"):
 if ni.get(k) is not True:E.append("non-interference:"+k)
act=c.get("activation",{})
for k in ("self_activation_forbidden","direct_active_forbidden","candidate_must_not_enter_active_rule_coverage"):
 if act.get(k) is not True:E.append("activation:"+k)
for x in ("positive_candidate_verification","destructive_test","independent_review","explicit_user_adoption","machine_enforced_registry_coverage"):
 if x not in act.get("requires_before_active",[]):E.append("activation prerequisite:"+x)
if s.get("status")!="CANDIDATE_SCHEMA":E.append("schema status")
for x in ("change_id","basis_head","target_head","purpose","change_type","affected_domains","planned_paths","forbidden_scope","authority","dimensions","approval","actual_diff","validation","independent_review","outcome"):
 if x not in s.get("required",[]):E.append("schema required:"+x)
if s.get("negative_conclusion",{}).get("single_zero_result_insufficient") is not True:E.append("schema zero-result escape")
reg=json.loads((R/"v2/gates/operational_rule_registry_v17.json").read_text())
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text())
rules={x.get("id"):x for x in reg.get("rules",[])}
if rules.get("CB6-DEVELOPMENT-AUDITOR-V1",{}).get("status")!="ACTIVE":E.append("ACTIVE V1 not preserved")
if cov.get("registry")!="v2/gates/operational_rule_registry_v17.json":E.append("coverage authority changed")
if E:
 print("CB6 DEVELOPMENT AUDITOR V2 CANDIDATE FAIL:",*E,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT AUDITOR V2 CANDIDATE PASS: work-unit execution evidence, semantic challenge, approval scope, independent review and zero-result sufficiency are fail-closed")
