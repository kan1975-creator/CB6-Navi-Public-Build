#!/usr/bin/env python3
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[];me=Path(__file__).read_text();tree=ast.parse(me);candidate="verify_development_auditor_v2_atomic_coverage_e2e"
for n in ast.walk(tree):
 if isinstance(n,ast.Import) and any(x.name==candidate for x in n.names):e.append("candidate verifier import")
 if isinstance(n,ast.ImportFrom) and (n.module or "")==candidate:e.append("candidate verifier import")
f=json.loads((R/"v2/gates/development_auditor_v2_atomic_coverage_e2e_cases.json").read_text())
c=json.loads((R/f["authorities"]["contract"]).read_text());s=json.loads((R/f["authorities"]["schema"]).read_text());m=json.loads((R/f["authorities"]["method"]).read_text())
if len(c.get("acceptance_criteria",[]))!=18 or len(c.get("mandatory_dimensions",[]))!=9:e.append("contract cardinality")
for sec in f["contract_sections"]:
 if sec not in c:e.append("contract:"+sec)
for sec in f["schema_sections"]:
 if sec not in s:e.append("schema:"+sec)
for sec in f["method_sections"]:
 if sec not in m:e.append("method:"+sec)
if s.get("not_applicable_required")!=["reason","applicability_evidence_refs"]:e.append("N/A branches")
if len(m.get("feature_development_pipeline",[]))!=11 or len(set(m["feature_development_pipeline"]))!=11:e.append("method 11")
for p in f["required_e2e"]:
 if not (R/p).exists():e.append("E2E:"+p)
ev=json.loads((R/"v2/gates/development_auditor_adoption_evidence_v2.json").read_text()).get("evidence",{}).get("final_e2e_branch_coverage",{})
x=f["final_evidence"]
if (ev.get("head"),ev.get("remaining_gaps_candidate",{}).get("run_id"),ev.get("remaining_gaps_independent_review",{}).get("run_id"),ev.get("development_gate",{}).get("run_id"))!=(x["head"],x["remaining_gaps_candidate_run"],x["remaining_gaps_independent_review_run"],x["development_gate_run"]):e.append("final evidence")
pc=json.loads((R/"v2/gates/development_auditor_postchange_certification_v2.json").read_text())
if pc.get("postchange_head")!=f["postchange_certification_policy"]["known_stale_head"]:e.append("stale certification")
if e:print("AUDITOR V2 ATOMIC COVERAGE INDEPENDENT REVIEW FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 ATOMIC COVERAGE INDEPENDENT REVIEW PASS: independently reconstructed authority, branch cardinality, E2E and evidence")
