#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_status_reporting_active_v12.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("v12 ACTIVE baseline failed")
cases=[
("inactive",lambda d:d.update({"status":"CANDIDATE"})),
("no-current-head",lambda d:d["response_execution_preflight"].update({"current_head_evidence_required":False})),
("no-active-rules",lambda d:d["response_execution_preflight"].update({"applicable_active_rules_evidence_required":False})),
("self-attestation",lambda d:d["response_execution_preflight"].update({"self_attestation_alone_forbidden":False})),
("no-cumulative-elapsed",lambda d:d["response_execution_preflight"]["wait"].update({"later_wait_requires_cumulative_elapsed_from_original_start":False})),
("no-next-check",lambda d:d["response_execution_preflight"]["wait"].update({"next_check_timing_required":False})),
("unsupported-time",lambda d:d["response_execution_preflight"]["wait"].update({"unsupported_time_estimate_forbidden":False})),
("nonterminal-summary",lambda d:d["response_execution_preflight"]["final_summary"].update({"must_be_response_end":False})),
("machine-overclaim",lambda d:d["response_execution_preflight"]["evidence_boundary"].update({"github_cannot_intercept_chatgpt_response_transmission":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/status_reporting_contract_v12.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("v12 ACTIVE destructive bypass:"+name)
  print("PASS expected ACTIVE rejection:",name)
print("CB6 STATUS REPORTING V12 ACTIVE DESTRUCTIVE PASS:",len(cases))
