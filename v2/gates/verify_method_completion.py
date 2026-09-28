#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(m):
 print("CB6 METHOD COMPLETION FAIL:",m); raise SystemExit(1)
d=json.loads((ROOT/"v2/gates/development_method_completion.json").read_text())
if d.get("schema")!=1 or d.get("status")!="COMPLETE": fail("method completion is not COMPLETE")
proof=d.get("proof",{})
required={"root_certified","method_frozen","design_coverage","repository_integrity","zero_omission"}
if set(proof)!=required or not all(v is True for v in proof.values()): fail("completion proof incomplete")
cmds={
 "method_frozen":[sys.executable,"v2/gates/verify_method_freeze.py"],
 "design_coverage":[sys.executable,"v2/gates/verify_design_coverage.py"],
 "repository_integrity":[sys.executable,"v2/gates/verify_project_integrity.py"],
 "zero_omission":[sys.executable,"v2/gates/verify_source_atomic_coverage.py"],
}
cert=json.loads((ROOT/"v2/gates/root_invariants.json").read_text())
if cert.get("certification",{}).get("status")!="CERTIFIED" or cert["certification"].get("feature_execution_permitted") is not True: fail("root certification is not persisted CERTIFIED")
for name,cmd in cmds.items():
 cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
 if cp.returncode: fail(name+" executable proof failed:\n"+cp.stdout+cp.stderr)
print("CB6 METHOD COMPLETION PASS: executable proof chain verified")
