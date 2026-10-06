#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];F=R/"v2/gates/development_auditor_v2_atomic_coverage_e2e_cases.json";f=json.loads(F.read_text());e=[]
A={k:json.loads((R/f["authorities"][k]).read_text()) for k in ("contract","schema","method")}
C=A["contract"];S=A["schema"];M=A["method"]
expected={
"acceptance_criteria":[f"AC-{i:02d} "+n for i,n in enumerate(["freshness","authority reconstruction","work-unit identity","applicability fail-closed","concrete research evidence","semantic challenge","prior-failure comparison","impact completeness","approval binding","scope-drift rejection","actual-diff comparison","validation evidence","independent semantic review","blocking disagreement rejection","exit audit","non-interference","existing-mechanism reuse","earliest-stage return"],1)],
"mandatory_dimensions":["freshness","active_authority","user_intent","applicable_rules_and_method","approval_boundary","change_impact","known_failures","actual_scope","unresolved_blockers"]}
for k,v in expected.items():
 if C.get(k)!=v:e.append("contract:"+k)
if C.get("applicability")!={"states":["APPLIED","NOT_APPLICABLE","BLOCKED"],"mandatory_not_applicable_forbidden":True,"conditional_not_applicable_requires_reason_and_evidence":True}:e.append("contract:applicability")
for sec in f["contract_sections"]:
 if sec not in C:e.append("missing contract section:"+sec)
for sec in f["schema_sections"]:
 if sec not in S:e.append("missing schema section:"+sec)
for sec in f["method_sections"]:
 if sec not in M:e.append("missing method section:"+sec)
if S.get("not_applicable_required")!=["reason","applicability_evidence_refs"]:e.append("schema:not_applicable_required")
if len(S.get("required",[]))!=15 or len(S.get("dimension_required",[]))!=7 or len(S.get("pass_requires",{}))!=9:e.append("schema cardinality")
if len(M.get("feature_development_pipeline",[]))!=11:e.append("method pipeline cardinality")
for p in f["required_e2e"]:
 if not (R/p).is_file():e.append("missing E2E:"+p)
ev=json.loads((R/"v2/gates/development_auditor_adoption_evidence_v2.json").read_text()).get("evidence",{}).get("final_e2e_branch_coverage",{})
fe=f["final_evidence"]
if ev.get("head")!=fe["head"] or ev.get("remaining_gaps_candidate",{}).get("run_id")!=fe["remaining_gaps_candidate_run"] or ev.get("remaining_gaps_independent_review",{}).get("run_id")!=fe["remaining_gaps_independent_review_run"] or ev.get("development_gate",{}).get("run_id")!=fe["development_gate_run"]:e.append("final evidence binding")
pc=json.loads((R/"v2/gates/development_auditor_postchange_certification_v2.json").read_text())
if f["postchange_certification_policy"]["stale_certification_must_not_be_treated_as_current"] is not True or pc.get("postchange_head")!=f["postchange_certification_policy"]["known_stale_head"]:e.append("stale certification classification")
if f["atomic_requirements"]["conditional_not_applicable_independent_defects"]!=["missing_reason","missing_applicability_evidence"]:e.append("N/A independent defects")
if f["atomic_requirements"]["development_method_each_pipeline_stage_independently_omittable"] is not True:e.append("pipeline atomic policy")
if e:print("AUDITOR V2 ATOMIC COVERAGE E2E FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 ATOMIC COVERAGE E2E PASS: authority structure, atomic branches, existing E2E and final evidence bound")
