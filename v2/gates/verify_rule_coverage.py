#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
reg=json.loads((R/"v2/gates/operational_rule_registry.json").read_text())
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text())
a={x["id"] for x in reg["rules"]}
b={x["rule_id"] for x in cov["entries"]}
errors=[]
for x in sorted(a-b): errors.append("registry rule missing from coverage: "+x)
for x in sorted(b-a): errors.append("coverage rule missing from registry: "+x)
for x in cov["entries"]:
 if x.get("coverage_status")!="MACHINE_ENFORCED": errors.append("unenforced rule: "+x["rule_id"])
if errors:
 print("CB6 RULE COVERAGE FAIL:")
 for e in errors: print(" -",e)
 raise SystemExit(1)
print(f"CB6 RULE COVERAGE PASS: registered={len(a)}; machine_enforced={len(b)}; unenforced=0; bidirectional_mismatch=0")
