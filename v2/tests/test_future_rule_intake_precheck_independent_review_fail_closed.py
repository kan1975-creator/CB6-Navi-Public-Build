#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
CMD=["python3","v2/gates/verify_future_rule_intake_precheck_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
base=run(SRC)
if base.returncode: raise SystemExit("baseline failed:\n"+base.stdout+base.stderr)
cases=[
 ("five-way-weakened",lambda d:d["pre_registration_check"].update({"required_classification":["already_governed","duplicate","extension_needed","new_rule_needed"]})),
 ("evidence-weakened",lambda d:d["pre_registration_check"].update({"evidence_required":["current GitHub HEAD","five-way classification"]})),
 ("chat-only-allowed",lambda d:d["pre_registration_check"].update({"chat_only_completion_forbidden":False})),
 ("auditor-handoff-weakened",lambda d:d["auditor_handoff"].update({"required_for":["new_rule_needed"]})),
 ("direct-active-allowed",lambda d:d.update({"direct_active_forbidden":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/future_rule_intake_precheck_candidate.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d))
  cp=run(r)
  if cp.returncode==0: raise SystemExit(name+" not rejected")
  print("PASS expected rejection:",name)
print("PASS Future Rule Intake independent-review destructive cases rejected")
