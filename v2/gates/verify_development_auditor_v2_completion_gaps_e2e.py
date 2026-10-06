#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[];f=json.loads((R/"v2/gates/development_auditor_v2_completion_gaps_e2e_cases.json").read_text());c={x["id"]:x for x in f["cases"]}
for k in ("CG-01A","CG-01B","CG-01C"):
 if c.get(k,{}).get("expected")!="STOP":e.append(k)
for k in ("CG-02A","CG-02B","CG-02C","CG-02D"):
 x=c.get(k,{}).get("scope_check",{})
 if c.get(k,{}).get("expected")!="STOP" or x.get("paths_within_planned") is not True or not (x.get("purpose_matches") is False or x.get("affected_domains_match") is False or x.get("forbidden_scope_entered") is True or x.get("rename_delete_semantically_safe") is False):e.append(k)
for k in ("CG-03A","CG-03B","CG-03C","CG-03D","CG-03E","CG-03F"):
 x=c.get(k,{}).get("independent_review_check",{})
 if c.get(k,{}).get("expected")!="STOP" or not (x.get("reconstructed_from_target_head") is False or x.get("reconstructed_from_work_unit") is False or x.get("reconstructed_from_active_authority") is False or x.get("reconstructed_from_raw_evidence") is False or x.get("reuses_candidate_conclusion") is True or x.get("reuses_candidate_intermediate_decision") is True):e.append(k)
if e:print("AUDITOR V2 COMPLETION GAPS E2E FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("AUDITOR V2 COMPLETION GAPS E2E PASS: 13 independent branches")
