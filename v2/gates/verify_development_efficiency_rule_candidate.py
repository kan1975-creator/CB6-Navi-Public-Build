#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/"v2/gates/development_efficiency_rule_candidate.json";d=json.loads(p.read_text());e=[]
if d.get("rule_id")!="OPS-DEVELOPMENT-EFFICIENCY-001" or d.get("status")!="PROPOSED":e.append("identity/status")
if d.get("scope")!="all_current_features_all_future_features_all_33_items_and_derivative_work":e.append("scope")
r=d.get("requirements",{})
for k in ("acceptance_criteria_fixed_before_implementation_or_diagnostic_apk","broad_read_only_investigation_precedes_device_only_checks","observation_points_bundled_across_relevant_execution_path_when_practical","actions_wait_allows_non_conflicting_read_only_parallel_work","unnecessary_additional_diagnostics_after_fixed_criteria_pass_forbidden","multiple_diagnostic_iterations_allowed_when_required_for_cause_isolation"):
 if r.get(k) is not True:e.append("requirement:"+k)
nw=set(d.get("non_weakening",[]))
for x in ("OPS-USER-APPROVAL-BEFORE-FIX-001","OPS-INDEPENDENT-ACCEPTANCE-001","Device Evidence","Method Freeze","Root Certification","existing Acceptance criteria"):
 if x not in nw:e.append("non-weakening:"+x)
ev=d.get("evidence",{})
if ev.get("signal_run")!=37133503973 or ev.get("signal_run_result")!="SUCCESS" or ev.get("device_acceptance")!="4/4 PASS":e.append("signal evidence")
lc=d.get("lifecycle",{})
if lc.get("direct_active_forbidden") is not True or lc.get("sequence")!=["PROPOSED","CANDIDATE_VERIFIED","INDEPENDENTLY_REVIEWED","EXPLICIT_USER_ADOPTED","ACTIVE_REFROZEN"]:e.append("lifecycle")
reg=json.loads((R/"v2/gates/operational_rule_registry_v10.json").read_text())
if reg.get("status")!="ACTIVE" or any(x.get("id")=="OPS-DEVELOPMENT-EFFICIENCY-001" for x in reg.get("rules",[])):e.append("active registry mutated prematurely")
if e:
 print("CB6 DEVELOPMENT EFFICIENCY CANDIDATE FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT EFFICIENCY CANDIDATE PASS")
