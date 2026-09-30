#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_rule_adoption_lifecycle.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
b=run(S)
if b.returncode: raise SystemExit("adoption lifecycle baseline failed\n"+b.stdout+b.stderr)
cases=[("chat-can-activate",lambda d:d["adoption_lifecycle"].update({"chat_declaration_is_not_transition_evidence":False}),"chat declaration accepted"),("direct-active",lambda d:d["adoption_lifecycle"].update({"direct_transition_to_active_forbidden":False}),"direct ACTIVE transition not forbidden"),("missing-gate-evidence",lambda d:d["adoption_lifecycle"]["transitions"]["IMPLEMENTED_UNVERIFIED"].update({"requires":["destructive_test_path"]}),"invalid transition contract: IMPLEMENTED_UNVERIFIED"),("missing-user-authority",lambda d:d["adoption_lifecycle"]["transitions"]["MACHINE_VERIFIED"].update({"requires":["coverage_status_MACHINE_ENFORCED"]}),"invalid transition contract: MACHINE_VERIFIED")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/operational_rule_registry_v2.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d))
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected adoption rejection:",name)
print("PASS adoption lifecycle destructive cases rejected")
