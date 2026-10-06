#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
f=json.loads((R/"v2/gates/development_auditor_v2_completion_gaps_e2e_cases.json").read_text())
a=json.loads((R/f["authorities"]["auditor"]).read_text())
w=json.loads((R/f["authorities"]["work_unit_schema"]).read_text())
m=json.loads((R/f["authorities"]["development_method"]).read_text())
if a.get("revision")!=2 or not a.get("evidence_sufficiency",{}).get("concrete_evidence_refs_required"):e.append("auditor evidence authority")
if not a.get("evidence_sufficiency",{}).get("cross_work_unit_evidence_reuse_without_explicit_binding_forbidden"):e.append("evidence binding authority")
if not a.get("exit_audit",{}).get("actual_diff_must_match_declared_scope"):e.append("scope authority")
ir=a.get("independent_review",{})
if not ir.get("must_reconstruct_from_target_head_work_unit_active_authority_and_raw_evidence"):e.append("review reconstruction authority")
if not {"actual_diff","affected_domains","planned_paths","forbidden_scope","purpose","independent_review"}.issubset(set(w.get("required",[]))):e.append("work unit authority")
if "change_impact_before_implementation" not in m.get("feature_development_pipeline",[]):e.append("method impact authority")
cases={x["id"]:x for x in f.get("cases",[])}
c=cases.get("CG-01A",{}).get("evidence_check",{})
if c.get("refs_nonempty") is not True or c.get("exists") is not False:e.append("CG-01A defect missing")
c=cases.get("CG-01B",{}).get("evidence_check",{})
if c.get("refs_nonempty") is not True or c.get("exists") is not True or c.get("target_matches") is not False:e.append("CG-01B defect missing")
c=cases.get("CG-01C",{}).get("evidence_check",{})
if c.get("refs_nonempty") is not True or c.get("exists") is not True or c.get("target_matches") is not True or c.get("semantically_supports_finding") is not False:e.append("CG-01C defect missing")
c=cases.get("CG-02",{}).get("scope_check",{})
if c.get("paths_within_planned") is not True or not (c.get("purpose_matches") is False or c.get("affected_domains_match") is False or c.get("forbidden_scope_entered") is True or c.get("rename_delete_semantically_safe") is False):e.append("CG-02 defect missing")
c=cases.get("CG-03",{}).get("independent_review_check",{})
if c.get("accepted") is not True or not (c.get("reconstructed_from_raw_evidence") is False or c.get("reuses_candidate_conclusion") is True or c.get("reuses_candidate_intermediate_decision") is True):e.append("CG-03 defect missing")
for x in ("CG-01A","CG-01B","CG-01C","CG-02","CG-03"):
 if cases.get(x,{}).get("expected")!="STOP":e.append(x+" expected")
if e:
 print("AUDITOR V2 COMPLETION GAPS E2E FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("AUDITOR V2 COMPLETION GAPS E2E PASS: CG-01A..C, CG-02..03")
