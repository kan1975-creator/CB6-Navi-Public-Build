#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v9.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v9 candidate baseline failed")
cases=[("no-every-response","required_before_every_cb6_progress_response"),("no-github-authority","github_current_authority_check_required"),("no-rule-selection","applicable_active_rules_must_be_selected"),("no-response-check","response_must_be_checked_against_selected_active_rules"),("allow-conflict","contradiction_must_fail_closed"),("leak-hidden-detail","normal_hidden_detail_policy_must_be_enforced"),("skip-final-format","final_summary_format_must_be_checked"),("memory-authority","chat_memory_alone_forbidden")]
for name,key in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps")); p=r/"v2/gates/status_reporting_contract_candidate_v9.json"; q=json.loads(p.read_text()); q["response_preflight"][key]=False; p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or "response preflight guard invalid" not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected response-preflight rejection:",name)
print("PASS status reporting v9 response-preflight destructive cases rejected")
