#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
c=json.loads((R/"v2/gates/development_efficiency_rule_candidate.json").read_text());r=json.loads((R/"v2/gates/development_efficiency_independent_review.json").read_text())
if r.get("status")!="PROPOSED" or r.get("subject")!="OPS-DEVELOPMENT-EFFICIENCY-001":e.append("review identity/status")
if r.get("basis_head")!="7825901f40dc2ee39e5003d15ddfcda9e655953f" or r.get("evidence",{}).get("candidate_gate_run")!=37135315388 or r.get("evidence",{}).get("candidate_gate_result")!="SUCCESS":e.append("candidate evidence")
req=c.get("requirements",{})
keys=("acceptance_criteria_fixed_before_implementation_or_diagnostic_apk","broad_read_only_investigation_precedes_device_only_checks","observation_points_bundled_across_relevant_execution_path_when_practical","actions_wait_allows_non_conflicting_read_only_parallel_work","unnecessary_additional_diagnostics_after_fixed_criteria_pass_forbidden")
for k in keys:
 if req.get(k) is not True:e.append("five requirements not preserved:"+k)
if req.get("multiple_diagnostic_iterations_allowed_when_required_for_cause_isolation") is not True:e.append("cause-isolation exception lost")
if c.get("scope")!="all_current_features_all_future_features_all_33_items_and_derivative_work":e.append("scope weakened")
needed={"OPS-USER-APPROVAL-BEFORE-FIX-001","OPS-INDEPENDENT-ACCEPTANCE-001","Device Evidence","Method Freeze","Root Certification","existing Acceptance criteria"}
if not needed.issubset(set(c.get("non_weakening",[]))):e.append("existing governance weakened")
if c.get("status")!="PROPOSED" or c.get("lifecycle",{}).get("direct_active_forbidden") is not True:e.append("candidate self activation")
for k in ("five_requirements_preserved","all_current_and_future_scope_preserved","existing_governance_non_weakening_preserved","self_activation_forbidden","candidate_verified","destructive_tests_passed","explicit_user_adoption_still_required"):
 if r.get("checks",{}).get(k) is not True:e.append("review check missing:"+k)
reg=json.loads((R/"v2/gates/operational_rule_registry_v10.json").read_text())
if reg.get("status")!="ACTIVE" or any(x.get("id")=="OPS-DEVELOPMENT-EFFICIENCY-001" for x in reg.get("rules",[])):e.append("ACTIVE registry changed before adoption")
if e:
 print("CB6 DEVELOPMENT EFFICIENCY INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT EFFICIENCY INDEPENDENT REVIEW PASS")
