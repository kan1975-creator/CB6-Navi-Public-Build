#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text())
reg_rel=cov.get("registry")
if not isinstance(reg_rel,str) or not reg_rel.startswith("v2/gates/operational_rule_registry_v") or ".." in reg_rel:
 print("CB6 RULE COVERAGE FAIL:\n - invalid registry pointer"); raise SystemExit(1)
reg_path=R/reg_rel
if not reg_path.is_file():
 print("CB6 RULE COVERAGE FAIL:\n - registry pointer target missing: "+reg_rel); raise SystemExit(1)
reg=json.loads(reg_path.read_text())
active={x["id"] for x in reg["rules"] if x.get("status")=="ACTIVE"}
proposed={x["id"] for x in reg["rules"] if x.get("status")=="PROPOSED"}
covered={x["rule_id"] for x in cov["entries"]}
errors=[]
for x in sorted(active-covered): errors.append("ACTIVE registry rule missing from coverage: "+x)
for x in sorted(covered-active): errors.append("coverage rule missing from registry: "+x)
for x in sorted(proposed & covered): errors.append("PROPOSED rule must not enter coverage: "+x)
for x in cov["entries"]:
 if x.get("coverage_status")!="MACHINE_ENFORCED": errors.append("unenforced rule: "+x["rule_id"])
aud=next((x for x in cov["entries"] if x.get("rule_id")=="CB6-DEVELOPMENT-AUDITOR-V2"),None)
if aud:
 reach=aud.get("enforcement_reachability",{})
 req={"active_verifier","work_unit_verifier","destructive_test","workflow_meta","feature_gate","candidate_workflow","independent_review_workflow","same_head_evidence"}
 if set(reach)!=req: errors.append("CB6-DEVELOPMENT-AUDITOR-V2 MACHINE_ENFORCED lacks exact runtime reachability map")
 else:
  for k,v in reach.items():
   if not isinstance(v,str) or not (R/v).is_file(): errors.append("Auditor V2 reachability target missing: "+k+" -> "+str(v))
if errors:
 print("CB6 RULE COVERAGE FAIL:")
 for e in errors: print(" -",e)
 raise SystemExit(1)
print(f"CB6 RULE COVERAGE PASS: active={len(active)}; proposed={len(proposed)}; machine_enforced={len(covered)}; mismatch=0")
