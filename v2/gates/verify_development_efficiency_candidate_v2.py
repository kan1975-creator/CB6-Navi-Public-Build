#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
old=json.loads((R/"v2/gates/development_efficiency_rule_candidate.json").read_text())
c=json.loads((R/"v2/gates/development_efficiency_rule_candidate_v2.json").read_text())
if old.get("status")!="ACTIVE": e.append("existing ACTIVE authority changed")
if c.get("status")!="PROPOSED" or c.get("revision")!=2: e.append("candidate identity")
if c.get("extends")!="v2/gates/development_efficiency_rule_candidate.json": e.append("extension binding")
for k,v in old.get("requirements",{}).items():
 if c.get("requirements",{}).get(k)!=v: e.append("existing requirement weakened:"+k)
need=["error_fix_proposal_requires_multi_angle_read_only_analysis","direct_cause_must_be_identified","error_introduction_cause_must_be_identified","missed_detection_cause_must_be_identified","impact_scope_must_be_checked","alternative_implementation_must_be_considered","recurrence_prevention_must_be_considered","minimum_fix_scope_must_be_defined","insufficient_cause_analysis_blocks_fix_proposal","analogous_current_and_future_feature_prevention_must_be_considered"]
for k in need:
 if c.get("requirements",{}).get(k) is not True:e.append("missing requirement:"+k)
dims=set(c.get("analysis_dimensions",[]))
for x in ["requirements_understanding","pinned_original_source","implementation_method","generation_and_application_order","string_or_data_transformation","cross_feature_composition","actual_workflow_execution_path","verifiers_and_destructive_tests","review_and_preflight_gaps","similar_prior_failures"]:
 if x not in dims:e.append("missing dimension:"+x)
ev=set(c.get("required_fix_proposal_evidence",[]))
for x in ["direct_cause","error_introduction_cause","missed_detection_cause","impact_scope","alternative_implementation","recurrence_prevention","minimum_fix_scope"]:
 if x not in ev:e.append("missing proposal evidence:"+x)
for x in ["OPS-USER-APPROVAL-BEFORE-FIX-001","OPS-INDEPENDENT-ACCEPTANCE-001","OPS-APK-BUILD-PREFLIGHT-001","Device Evidence","Method Freeze","Root Certification","existing Acceptance criteria"]:
 if x not in c.get("non_weakening",[]):e.append("non-weakening missing:"+x)
if c.get("lifecycle",{}).get("direct_active_forbidden") is not True:e.append("direct ACTIVE not forbidden")
if e:
 print("CB6 DEVELOPMENT EFFICIENCY V2 CANDIDATE FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT EFFICIENCY V2 CANDIDATE PASS")
