#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/development_auditor_candidate_v2.json").read_text())
if d.get("revision")!=2 or d.get("status")!="CANDIDATE":e.append("V2 contract identity")
for n in range(1,19):
 if not any(x.startswith(f"AC-{n:02d} ") for x in d.get("acceptance_criteria",[])):e.append(f"missing AC-{n:02d}")
if d.get("evidence_sufficiency",{}).get("negative_conclusion_from_single_zero_result_forbidden") is not True:e.append("zero-result sufficiency")
if d.get("independent_review",{}).get("blocking_disagreement_forbids_pass") is not True:e.append("blocking disagreement")
if d.get("approval",{}).get("scope_expansion_requires_new_bound_approval") is not True:e.append("approval scope drift")
ev=json.loads((R/"v2/gates/development_auditor_adoption_evidence_v2.json").read_text())
if ev.get("status")!="ACTIVE" or ev.get("subject")!="CB6-DEVELOPMENT-AUDITOR-V2":e.append("V2 adoption")
if ev.get("evidence",{}).get("candidate_gate",{}).get("run_id")!=37405936430:e.append("candidate evidence")
if ev.get("evidence",{}).get("independent_review",{}).get("run_id")!=37406142902:e.append("review evidence")
ie2e=ev.get("evidence",{}).get("incident_e2e_candidate",{})
if ie2e.get("run_id")!=37410918733 or ie2e.get("conclusion")!="success" or ie2e.get("candidate_head")!="599dccca73b6dfe646672c6af0ad8ffffaac24ab":e.append("incident E2E candidate evidence")
iir=ev.get("evidence",{}).get("incident_e2e_independent_review",{})
if iir.get("run_id")!=37411289491 or iir.get("conclusion")!="success" or iir.get("candidate_head")!="871550b34d9e6d080f58a1a18e08cce606d75aae":e.append("incident E2E independent review evidence")
sfe=ev.get("evidence",{}).get("stage_forgetting_e2e_candidate",{})
if sfe.get("run_id")!=37415772275 or sfe.get("conclusion")!="success" or sfe.get("candidate_head")!="10d6ca132dd0787555710e0000a79dfd3778cb4f":e.append("stage forgetting E2E candidate evidence")
sfir=ev.get("evidence",{}).get("stage_forgetting_e2e_independent_review",{})
if sfir.get("run_id")!=37416002831 or sfir.get("conclusion")!="success" or sfir.get("candidate_head")!="72e28c4a6093f43231dee0bf1b94e8bf8f82f641":e.append("stage forgetting E2E independent review evidence")
reg=json.loads((R/"v2/gates/operational_rule_registry_v19.json").read_text());cov=json.loads((R/"v2/gates/rule_coverage.json").read_text())
rr=[x for x in reg.get("rules",[]) if x.get("id")=="CB6-DEVELOPMENT-AUDITOR-V2"]
if len(rr)!=1 or rr[0].get("status")!="ACTIVE" or rr[0].get("contract")!="v2/gates/development_auditor_candidate_v2.json":e.append("V2 registry activation")
if any(x.get("id")=="CB6-DEVELOPMENT-AUDITOR-V1" for x in reg.get("rules",[])):e.append("V1 still active in v19")
if cov.get("registry")!="v2/gates/operational_rule_registry_v19.json":e.append("coverage registry")
if not any(x.get("rule_id")=="CB6-DEVELOPMENT-AUDITOR-V2" and x.get("coverage_status")=="MACHINE_ENFORCED" for x in cov.get("entries",[])):e.append("V2 coverage")
if any(x.get("rule_id")=="CB6-DEVELOPMENT-AUDITOR-V1" for x in cov.get("entries",[])):e.append("V1 coverage still current")
if e:
 print("CB6 DEVELOPMENT AUDITOR V2 ACTIVE FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("CB6 DEVELOPMENT AUDITOR V2 ACTIVE PASS: adopted V2 authority, AC-01..18, semantic evidence, approval scope and machine coverage preserved")
