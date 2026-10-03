#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PLAN=ROOT/"v2/gates/root_certification_plan.json"
def fail(m):
 print("CB6 ROOT CERTIFICATION FAIL:",m); raise SystemExit(1)
plan=json.loads(PLAN.read_text())
if plan.get("schema")!=1: fail("plan schema invalid")
proofs=plan.get("proofs",{})
required={"context_loss","missing_state","permission_fail_closed","repository_reconstruction","historical_incidents","unknown_change","independent_verification","extensibility","artifact_identity","device_evidence","zero_omission"}
if set(proofs)!=required: fail("proof set incomplete")
results={}
for name in sorted(required):
 cmd=proofs[name].get("command")
 if not isinstance(cmd,list) or not cmd or any(not isinstance(x,str) or not x for x in cmd): fail("invalid proof command: "+name)
 cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
 if cp.returncode:
  fail(name+" proof failed:\n"+cp.stdout+cp.stderr)
 results[name]=True
print(json.dumps({"schema":1,"status":"PROVEN","proof":results},sort_keys=True))
