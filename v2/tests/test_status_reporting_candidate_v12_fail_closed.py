#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v12.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("v12 candidate baseline failed")
cases=[
("allow-self-attestation",lambda d:d["response_execution_preflight"].update({"self_attestation_alone_forbidden":False})),
("drop-active-rules",lambda d:d["response_execution_preflight"].update({"applicable_active_rules_evidence_required":False})),
("drop-cumulative-elapsed",lambda d:d["response_execution_preflight"]["wait"].update({"later_wait_requires_cumulative_elapsed_from_original_start":False})),
("drop-next-check",lambda d:d["response_execution_preflight"]["wait"].update({"next_check_timing_required":False})),
("allow-unsupported-time",lambda d:d["response_execution_preflight"]["wait"].update({"unsupported_time_estimate_forbidden":False})),
("drop-parallel-work",lambda d:d["response_execution_preflight"]["wait"].update({"parallel_work_availability_required":False})),
("drop-post-wait",lambda d:d["response_execution_preflight"]["wait"].update({"post_wait_instruction_required":False})),
("allow-nonterminal-summary",lambda d:d["response_execution_preflight"]["final_summary"].update({"must_be_response_end":False})),
("overclaim-machine-intercept",lambda d:d["response_execution_preflight"]["evidence_boundary"].update({"github_cannot_intercept_chatgpt_response_transmission":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/status_reporting_contract_candidate_v12.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("v12 destructive case passed: "+name)
  print("PASS expected v12 rejection:",name)
print("CB6 STATUS REPORTING V12 CANDIDATE DESTRUCTIVE PASS:",len(cases))
