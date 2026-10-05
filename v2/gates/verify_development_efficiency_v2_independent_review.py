#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
old=json.loads((R/"v2/gates/development_efficiency_rule_candidate.json").read_text())
c=json.loads((R/"v2/gates/development_efficiency_rule_candidate_v2.json").read_text())
reg=json.loads((R/"v2/gates/operational_rule_registry_v14.json").read_text())
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text())
if old.get("status")!="ACTIVE":e.append("existing efficiency authority not ACTIVE")
if c.get("status")!="PROPOSED" or c.get("revision")!=2:e.append("candidate lifecycle/identity")
if c.get("extends")!="v2/gates/development_efficiency_rule_candidate.json":e.append("candidate not bound as extension")
for k,v in old.get("requirements",{}).items():
 if c.get("requirements",{}).get(k)!=v:e.append("existing requirement changed:"+k)
r={x["id"]:x for x in reg.get("rules",[])}
if r.get("OPS-DEVELOPMENT-EFFICIENCY-001",{}).get("status")!="ACTIVE":e.append("registry current rule")
if cov.get("registry")!="v2/gates/operational_rule_registry_v14.json":e.append("coverage authority")
must={
 "error_fix_proposal_requires_multi_angle_read_only_analysis",
 "direct_cause_must_be_identified","error_introduction_cause_must_be_identified",
 "missed_detection_cause_must_be_identified","impact_scope_must_be_checked",
 "alternative_implementation_must_be_considered","recurrence_prevention_must_be_considered",
 "minimum_fix_scope_must_be_defined","insufficient_cause_analysis_blocks_fix_proposal",
 "analogous_current_and_future_feature_prevention_must_be_considered"}
if any(c.get("requirements",{}).get(x) is not True for x in must):e.append("required multi-angle controls incomplete")
dims=set(c.get("analysis_dimensions",[]))
if not {"requirements_understanding","pinned_original_source","implementation_method","generation_and_application_order","string_or_data_transformation","cross_feature_composition","actual_workflow_execution_path","verifiers_and_destructive_tests","review_and_preflight_gaps","similar_prior_failures"}.issubset(dims):e.append("analysis dimensions incomplete")
ev=set(c.get("required_fix_proposal_evidence",[]))
if not {"direct_cause","error_introduction_cause","missed_detection_cause","impact_scope","alternative_implementation","recurrence_prevention","minimum_fix_scope"}.issubset(ev):e.append("proposal evidence incomplete")
if c.get("lifecycle",{}).get("direct_active_forbidden") is not True:e.append("direct activation escape")
if e:
 print("CB6 DEVELOPMENT EFFICIENCY V2 INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT EFFICIENCY V2 INDEPENDENT REVIEW PASS: extension preserves ACTIVE authority and requires cause/origin/detection/prevention evidence")
