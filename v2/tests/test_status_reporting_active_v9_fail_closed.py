#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_active_v9.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v9 baseline failed")
cases=[("no-every-response",lambda q:q["response_preflight"].update({"required_before_every_cb6_progress_response":False}),"response preflight guard invalid"),("claim-interception",lambda q:q["response_preflight"]["enforcement_model"].update({"github_does_not_guarantee_response_transmission_interception":False}),"response preflight enforcement boundary invalid"),("unlimited-machine-claim",lambda q:q["response_preflight"]["enforcement_model"].update({"machine_enforced_claim_limited_to_repository_contract_and_verification":False}),"response preflight enforcement boundary invalid"),("drop-runtime",lambda q:q["response_preflight"]["enforcement_model"]["chatgpt_runtime_responsibility"].remove("perform_preflight_before_each_CB6_progress_response"),"runtime responsibility missing"),("drop-github-boundary",lambda q:q["response_preflight"]["enforcement_model"]["github_machine_verifiable"].remove("contract_fields_and_scope"),"github-verifiable boundary missing"),("pending-activation",lambda q:q["activation"].update({"status":"ACTIVE_PENDING_REFREEZE"}),"activation lifecycle not finalized"),("pending-adoption",lambda q:q["adoption"].update({"status":"ADOPTED_PENDING_REFREEZE"}),"adoption lifecycle not finalized")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps")); p=r/"v2/gates/status_reporting_contract_v9.json"; q=json.loads(p.read_text()); mut(q); p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected response-preflight rejection:",name)
print("PASS status reporting v9 enforcement-boundary destructive cases rejected")
