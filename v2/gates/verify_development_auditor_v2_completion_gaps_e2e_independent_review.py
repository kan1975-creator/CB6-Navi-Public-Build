#!/usr/bin/env python3
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
SELF=Path(__file__).read_text();tree=ast.parse(SELF)
candidate_module="_".join(("verify","development","auditor","v2","completion","gaps","e2e"))
for n in ast.walk(tree):
 if isinstance(n,ast.Import):
  if any(x.name==candidate_module or x.name.startswith(candidate_module+".") for x in n.names):e.append("candidate verifier import forbidden")
 elif isinstance(n,ast.ImportFrom):
  mod=n.module or ""
  if mod==candidate_module or mod.startswith(candidate_module+"."):e.append("candidate verifier import forbidden")
 elif isinstance(n,ast.Call):
  fn=n.func
  if isinstance(fn,ast.Name) and fn.id in {"exec","eval","compile","__import__"}:
   if any(isinstance(a,ast.Constant) and isinstance(a.value,str) and candidate_module in a.value for a in n.args):e.append("candidate verifier execution forbidden")
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
x=c.get("CG-01A",{}).get("evidence_check",{})
if x.get("refs_nonempty") is not True or x.get("exists") is not False:e.append("CG-01A not independently proven")
x=c.get("CG-01B",{}).get("evidence_check",{})
if x.get("refs_nonempty") is not True or x.get("exists") is not True or x.get("target_matches") is not False:e.append("CG-01B not independently proven")
x=c.get("CG-01C",{}).get("evidence_check",{})
if x.get("refs_nonempty") is not True or x.get("exists") is not True or x.get("target_matches") is not True or x.get("semantically_supports_finding") is not False:e.append("CG-01C not independently proven")
x=c.get("CG-02",{}).get("scope_check",{})
if x.get("paths_within_planned") is not True or not (x.get("purpose_matches") is False or x.get("affected_domains_match") is False or x.get("forbidden_scope_entered") is True or x.get("rename_delete_semantically_safe") is False):e.append("CG-02 not independently proven")
x=c.get("CG-03",{}).get("independent_review_check",{})
required=("reconstructed_from_target_head","reconstructed_from_work_unit","reconstructed_from_active_authority")
if not all(x.get(k) is True for k in required):e.append("CG-03 reconstruction inputs")
if not (x.get("reconstructed_from_raw_evidence") is False or x.get("reuses_candidate_conclusion") is True or x.get("reuses_candidate_intermediate_decision") is True):e.append("CG-03 independence defect absent")
for k in ("CG-01A","CG-01B","CG-01C","CG-02","CG-03"):
 if c.get(k,{}).get("expected")!="STOP":e.append(k+" expected")
if e:
 print("AUDITOR V2 COMPLETION GAPS INDEPENDENT REVIEW FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("AUDITOR V2 COMPLETION GAPS INDEPENDENT REVIEW PASS: CG-01A..C, CG-02..03 independently reconstructed")
