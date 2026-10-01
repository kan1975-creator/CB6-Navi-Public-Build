#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
reg=json.loads((R/"v2/gates/operational_rule_registry_v4.json").read_text())
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text())
active={x["id"] for x in reg["rules"] if x.get("status")=="ACTIVE"}
proposed={x["id"] for x in reg["rules"] if x.get("status")=="PROPOSED"}
covered={x["rule_id"] for x in cov["entries"]}
errors=[]
for x in sorted(active-covered): errors.append("ACTIVE registry rule missing from coverage: "+x)
for x in sorted(covered-active): errors.append("coverage rule missing from registry: "+x)
for x in sorted(proposed & covered): errors.append("PROPOSED rule must not enter coverage: "+x)
for x in cov["entries"]:
 if x.get("coverage_status")!="MACHINE_ENFORCED": errors.append("unenforced rule: "+x["rule_id"])
if errors:
 print("CB6 RULE COVERAGE FAIL:")
 for e in errors: print(" -",e)
 raise SystemExit(1)
print(f"CB6 RULE COVERAGE PASS: active={len(active)}; proposed={len(proposed)}; machine_enforced={len(covered)}; mismatch=0")
