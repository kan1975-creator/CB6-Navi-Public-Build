#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];src=R/"v2/gates/development_efficiency_rule_candidate.json";base=json.loads(src.read_text());cases=[]
def add(n,fn):d=json.loads(json.dumps(base));fn(d);cases.append((n,d))
add("future_scope",lambda d:d.__setitem__("scope","current_features_only"))
for k in list(base["requirements"]):add("off_"+k,lambda d,k=k:d["requirements"].__setitem__(k,False))
add("approval_weakened",lambda d:d["non_weakening"].remove("OPS-USER-APPROVAL-BEFORE-FIX-001"))
add("independent_weakened",lambda d:d["non_weakening"].remove("OPS-INDEPENDENT-ACCEPTANCE-001"))
add("device_weakened",lambda d:d["non_weakening"].remove("Device Evidence"))
add("method_weakened",lambda d:d["non_weakening"].remove("Method Freeze"))
add("root_weakened",lambda d:d["non_weakening"].remove("Root Certification"))
add("acceptance_weakened",lambda d:d["non_weakening"].remove("existing Acceptance criteria"))
add("direct_active",lambda d:d["lifecycle"].__setitem__("direct_active_forbidden",False))
for name,d in cases:
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);shutil.copytree(R/"v2",t/"v2");(t/"v2/gates/development_efficiency_rule_candidate.json").write_text(json.dumps(d,indent=2))
  p=subprocess.run(["python3",str(t/"v2/gates/verify_development_efficiency_rule_candidate.py")],cwd=t,capture_output=True,text=True)
  if p.returncode==0:raise SystemExit("destructive case unexpectedly passed: "+name)
print("CB6 DEVELOPMENT EFFICIENCY DESTRUCTIVE PASS:",len(cases),"weakenings rejected")
