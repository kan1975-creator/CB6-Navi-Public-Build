#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
CMD=["python3","v2/gates/verify_future_rule_intake_precheck_candidate.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
base=run(SRC)
if base.returncode: raise SystemExit("baseline failed:\n"+base.stdout+base.stderr)
cases=[
 ("duplicate-allowed",lambda d:d["pre_registration_check"]["outcomes"].update({"exact_duplicate":"CREATE_NEW_RULE"}),"exact duplicate does not block"),
 ("candidate-scope-omitted",lambda d:d["pre_registration_check"].update({"search_scope":["ACTIVE operational rules","development method authority","governance and cross-cutting rules"]}),"search scope incomplete"),
 ("chat-memory-allowed",lambda d:d["pre_registration_check"].update({"chat_memory_only_forbidden":False}),"chat-memory-only precheck allowed"),
 ("direct-active",lambda d:d.update({"status":"ACTIVE"}),"candidate must remain PROPOSED")
]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/future_rule_intake_precheck_candidate.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d))
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected correctly:\n"+out)
  print("PASS expected rejection:",name)
print("PASS future-rule intake precheck destructive cases rejected")
