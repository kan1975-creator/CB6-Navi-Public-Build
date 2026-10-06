#!/usr/bin/env python3
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
SELF=Path(__file__).read_text();tree=ast.parse(SELF)
for n in ast.walk(tree):
 if isinstance(n,(ast.Import,ast.ImportFrom)):e.append("independent review must not import candidate verifier")
 if isinstance(n,ast.Constant) and isinstance(n.value,str) and "verify_development_auditor_v2_completion_gaps_e2e.py" in n.value:e.append("candidate verifier execution/reference forbidden")
f=json.loads((R/"v2/gates/development_auditor_v2_completion_gaps_e2e_cases.json").read_text())
a=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
w=json.loads((R/"v2/gates/development_auditor_work_unit_schema_v1.json").read_text())
m=json.loads((R/"v2/gates/development_method_contract.json").read_text())
if not a.get("evidence_sufficiency",{}).get("concrete_evidence_refs_required"):e.append("evidence authority")
if not a.get("evidence_sufficiency",{}).get("cross_work_unit_evidence_reuse_without_explicit_binding_forbidden"):e.append("binding authority")
if not a.get("exit_audit",{}).get("actual_diff_must_match_declared_scope"):e.append("scope authority")
if not a.get("independent_review",{}).get("must_reconstruct_from_target_head_work_unit_active_authority_and_raw_evidence"):e.append("review authority")
if not {"purpose","affected_domains","planned_paths","forbidden_scope","actual_diff","independent_review"}.issubset(w.get("required",[])):e.append("schema authority")
if "change_impact_before_implementation" not in m.get("feature_development_pipeline",[]):e.append("method authority")
c={x["id"]:x for x in f.get("cases",[])}
x=c.get("CG-01",{}).get("evidence_check",{})
if x.get("refs_nonempty") is not True or not (x.get("exists") is False or x.get("work_unit_bound") is False or x.get("target_matches") is False or x.get("semantically_supports_finding") is False):e.append("CG-01 not independently proven")
x=c.get("CG-02",{}).get("scope_check",{})
if x.get("paths_within_planned") is not True or not (x.get("purpose_matches") is False or x.get("affected_domains_match") is False or x.get("forbidden_scope_entered") is True or x.get("rename_delete_semantically_safe") is False):e.append("CG-02 not independently proven")
x=c.get("CG-03",{}).get("independent_review_check",{})
required=("reconstructed_from_target_head","reconstructed_from_work_unit","reconstructed_from_active_authority")
if not all(x.get(k) is True for k in required):e.append("CG-03 reconstruction inputs")
if not (x.get("reconstructed_from_raw_evidence") is False or x.get("reuses_candidate_conclusion") is True or x.get("reuses_candidate_intermediate_decision") is True):e.append("CG-03 independence defect absent")
for k in ("CG-01","CG-02","CG-03"):
 if c.get(k,{}).get("expected")!="STOP":e.append(k+" expected")
if e:
 print("AUDITOR V2 COMPLETION GAPS INDEPENDENT REVIEW FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("AUDITOR V2 COMPLETION GAPS INDEPENDENT REVIEW PASS: CG-01..03 independently reconstructed")
