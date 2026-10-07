#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_future_rule_intake_precheck_active.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("ACTIVE baseline failed")
cases=[
("inactive",lambda d:d.update({"status":"PROPOSED"})),
("five-way-weakened",lambda d:d["pre_registration_check"].update({"required_classification":["already_governed","duplicate","extension_needed","new_rule_needed"]})),
("evidence-weakened",lambda d:d["pre_registration_check"].update({"evidence_required":["current GitHub HEAD","five-way classification"]})),
("chat-only-allowed",lambda d:d["pre_registration_check"].update({"chat_only_completion_forbidden":False})),
("handoff-weakened",lambda d:d["auditor_handoff"].update({"required_for":["new_rule_needed"]})),
("direct-active-guard-removed",lambda d:d.update({"direct_active_forbidden":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/future_rule_intake_precheck_active.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d))
  if run(r).returncode==0:raise SystemExit("ACTIVE destructive bypass:"+name)
  print("PASS expected ACTIVE rejection:",name)
print("PASS Future Rule Intake ACTIVE destructive cases rejected")
