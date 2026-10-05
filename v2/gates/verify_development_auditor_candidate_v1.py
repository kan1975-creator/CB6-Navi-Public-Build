#!/usr/bin/env python3
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
E = []
P = R / "v2/gates/development_auditor_candidate_v1.json"
D = json.loads(P.read_text(encoding="utf-8"))

if D.get("id") != "CB6-DEVELOPMENT-AUDITOR-V1" or D.get("status") != "CANDIDATE":
    E.append("candidate identity/status invalid")

fresh = D.get("freshness", {})
for k in ("latest_head_required_each_audit", "active_authority_refetch_required_each_audit", "chat_memory_is_not_authority", "head_change_requires_resynchronization"):
    if fresh.get(k) is not True:
        E.append("freshness guard missing: " + k)

reuse = D.get("reuse", {})
if reuse.get("existing_mechanisms_preferred") is not True or reuse.get("duplicate_mechanism_forbidden_when_existing_mechanism_is_sufficient") is not True:
    E.append("existing mechanism reuse not fail-closed")

required_dimensions = {
    "rules","specifications","lists_and_worklists","change_bound_approval","multidirectional_research",
    "change_impact","implementation_and_validation_scope","atomic_and_traceability","evidence",
    "known_failures_and_regressions"
}
missing = required_dimensions - set(D.get("audit_dimensions", []))
if missing:
    E.append("audit dimensions missing: " + ",".join(sorted(missing)))

for rel in D.get("required_existing_sources", []):
    if not (R / rel).exists():
        E.append("required existing source missing: " + rel)

ab = D.get("approval_boundary", {})
if ab.get("rule_id") != "OPS-USER-APPROVAL-BEFORE-FIX-001":
    E.append("approval authority binding invalid")
for k in ("post_hoc_approval_forbidden", "read_only_research_and_design_may_continue_without_change_approval", "specific_change_requires_change_bound_approval_before_implementation"):
    if ab.get(k) is not True:
        E.append("approval boundary invalid: " + k)
if ab.get("unknown_future_change_may_reuse_prior_approval") is not False:
    E.append("unknown future approval reuse not forbidden")

if set(D.get("outcomes", {})) != {"STOP","CORRECT","FOLLOW-UP","PASS"}:
    E.append("audit outcomes must be exactly STOP/CORRECT/FOLLOW-UP/PASS")

ni = D.get("non_interference", {})
for k in ("application_source_change_forbidden","signal_behavior_change_forbidden","convenience_behavior_change_forbidden","search_routing_renderer_change_forbidden","existing_independent_review_weaken_forbidden","existing_gate_or_evidence_weaken_forbidden"):
    if ni.get(k) is not True:
        E.append("non-interference guard missing: " + k)

act = D.get("activation", {})
for k in ("self_activation_forbidden","direct_active_forbidden","candidate_must_not_enter_active_rule_coverage"):
    if act.get(k) is not True:
        E.append("activation guard missing: " + k)
for x in ("positive_candidate_verification","destructive_test","independent_review","explicit_user_adoption","machine_enforced_registry_coverage"):
    if x not in act.get("requires_before_active", []):
        E.append("activation prerequisite missing: " + x)

reg = json.loads((R / "v2/gates/operational_rule_registry_v16.json").read_text(encoding="utf-8"))
cov = json.loads((R / "v2/gates/rule_coverage.json").read_text(encoding="utf-8"))
if reg.get("status") != "ACTIVE" or reg.get("version") != 16:
    E.append("current ACTIVE registry is not v16")
if cov.get("registry") != "v2/gates/operational_rule_registry_v16.json":
    E.append("current rule coverage registry binding invalid")
if any(x.get("rule_id") == "CB6-DEVELOPMENT-AUDITOR-V1" for x in cov.get("entries", [])):
    E.append("candidate illegally entered ACTIVE rule coverage")

method = json.loads((R / "v2/gates/development_method_contract.json").read_text(encoding="utf-8"))
if method.get("method_version") != 2:
    E.append("development method v2 not preserved")

if E:
    print("CB6 DEVELOPMENT AUDITOR CANDIDATE FAIL:")
    for x in E:
        print(" -", x)
    raise SystemExit(1)

print("CB6 DEVELOPMENT AUDITOR CANDIDATE PASS: existing authority reused; approval/freshness/non-interference/outcome guards intact; candidate not self-activated")
