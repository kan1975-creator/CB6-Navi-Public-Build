#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]
def run(r): return subprocess.run(["python3","v2/gates/verify_rule_coverage.py"],cwd=r,text=True,capture_output=True)
base=run(S)
if base.returncode: raise SystemExit("coverage baseline failed\n"+base.stdout+base.stderr)
for name,side,needle in [
 ("registry-only","registry","registry rule missing from coverage"),
 ("coverage-only","coverage","coverage rule missing from registry"),
 ("unenforced","unenforced","unenforced rule")]:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  if side=="registry":
   p=r/"v2/gates/operational_rule_registry_v2.json"; d=json.loads(p.read_text()); d["rules"].append({"id":"TEST-RULE-X","status":"ACTIVE","scope":"test","source":"test","contract":"v2/gates/development_method_contract.json","verification":["v2/gates/verify_rule_coverage.py"]}); p.write_text(json.dumps(d))
  else:
   p=r/"v2/gates/rule_coverage.json"; d=json.loads(p.read_text())
   if side=="coverage": d["entries"].append({"rule_id":"TEST-RULE-X","coverage_status":"MACHINE_ENFORCED"})
   else: d["entries"][0]["coverage_status"]="UNENFORCED"
   p.write_text(json.dumps(d))
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected coverage rejection:",name,"=>",needle)
print("PASS rule coverage bidirectional destructive cases rejected")
