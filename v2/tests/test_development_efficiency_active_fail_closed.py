#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];cases=[]
def add(n,p,fn):d=json.loads((R/p).read_text());fn(d);cases.append((n,p,d))
add("demote","v2/gates/operational_rule_registry_v11.json",lambda d:[x.update({"status":"PROPOSED"}) for x in d["rules"] if x["id"]=="OPS-DEVELOPMENT-EFFICIENCY-001"])
add("scope","v2/gates/operational_rule_registry_v11.json",lambda d:[x.update({"scope":"current_only"}) for x in d["rules"] if x["id"]=="OPS-DEVELOPMENT-EFFICIENCY-001"])
add("coverage","v2/gates/rule_coverage.json",lambda d:[x.update({"coverage_status":"DOCUMENTED_ONLY"}) for x in d["entries"] if x["rule_id"]=="OPS-DEVELOPMENT-EFFICIENCY-001"])
add("adoption","v2/gates/development_efficiency_adoption_evidence.json",lambda d:d["authority"].update({"decision":"missing"}))
add("old-rule","v2/gates/operational_rule_registry_v11.json",lambda d:d["rules"][0].update({"status":"PROPOSED"}))
for name,p,d in cases:
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);shutil.copytree(R/"v2",t/"v2");(t/p).write_text(json.dumps(d,ensure_ascii=False,indent=2))
  cp=subprocess.run(["python3",str(t/"v2/gates/verify_development_efficiency_active.py")],cwd=t,capture_output=True,text=True)
  if cp.returncode==0:raise SystemExit("destructive case unexpectedly passed: "+name)
print("CB6 DEVELOPMENT EFFICIENCY ACTIVE DESTRUCTIVE PASS:",len(cases),"weakenings rejected")
