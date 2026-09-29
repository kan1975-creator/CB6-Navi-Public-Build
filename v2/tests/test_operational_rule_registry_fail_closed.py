#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_operational_rule_registry.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(SRC).returncode: raise SystemExit("rule registry baseline failed")
cases=[
 ("future-active-without-verifier",{"id":"OPS-FUTURE-BAD","status":"ACTIVE","scope":"future","source":"user_continuing_instruction","contract":"v2/gates/operational_rule_registry.json","verification":[]},"lacks machine verification"),
 ("active-with-non-repository-verification-source",{"id":"OPS-FUTURE-BAD","status":"ACTIVE","scope":"future","source":"user_continuing_instruction","contract":"v2/gates/operational_rule_registry.json","verification":["chat:self-report"]},"verification source is not a GitHub repository path"),
 ("missing-contract",{"id":"OPS-FUTURE-BAD","status":"ACTIVE","scope":"future","source":"user_continuing_instruction","contract":"v2/gates/does-not-exist.json","verification":["v2/gates/verify_operational_rule_registry.py"]},"contract missing")
]
for name,row,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/operational_rule_registry.json"; d=json.loads(p.read_text()); d["rules"].append(row); p.write_text(json.dumps(d))
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected correctly:\n"+out)
  print("PASS expected future-rule rejection:",name)
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
 p=r/"v2/gates/operational_rule_registry.json"; d=json.loads(p.read_text()); d["rules"].append({"id":"OPS-FUTURE-PROPOSED","status":"PROPOSED","scope":"future","source":"user_continuing_instruction"}); p.write_text(json.dumps(d))
 cp=run(r)
 if cp.returncode: raise SystemExit("PROPOSED rule was incorrectly rejected:\n"+cp.stdout+cp.stderr)
 print("PASS unverifiable future rule remains PROPOSED")
print("PASS operational rule registry destructive cases rejected")
