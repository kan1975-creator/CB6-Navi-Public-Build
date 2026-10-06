#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_status_reporting_v12_independent_review.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("v12 independent baseline failed")
cases=[
("no-active-rule-evidence",lambda d:d["response_execution_preflight"].update({"applicable_active_rules_evidence_required":False})),
("self-attestation-pass",lambda d:d["response_execution_preflight"].update({"self_attestation_alone_forbidden":False})),
("missing-cumulative-elapsed",lambda d:d["response_execution_preflight"]["wait"].update({"later_wait_requires_cumulative_elapsed_from_original_start":False})),
("missing-next-check",lambda d:d["response_execution_preflight"]["wait"].update({"next_check_timing_required":False})),
("unsupported-time",lambda d:d["response_execution_preflight"]["wait"].update({"unsupported_time_estimate_forbidden":False})),
("missing-parallel-work",lambda d:d["response_execution_preflight"]["wait"].update({"parallel_work_availability_required":False})),
("missing-post-wait",lambda d:d["response_execution_preflight"]["wait"].update({"post_wait_instruction_required":False})),
("four-lines-not-terminal",lambda d:d["response_execution_preflight"]["final_summary"].update({"must_be_response_end":False})),
("claim-github-intercepts-chat",lambda d:d["response_execution_preflight"]["evidence_boundary"].update({"github_cannot_intercept_chatgpt_response_transmission":False})),
("allow-active-v11-change",lambda d:d["non_interference"].update({"active_v11_change_forbidden":False})),
("allow-app-change",lambda d:d["non_interference"].update({"application_behavior_change_forbidden":False}))
]
for name,mut in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/status_reporting_contract_candidate_v12.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("v12 independent bypass passed:"+name)
  print("PASS expected independent rejection:",name)
print("CB6 STATUS REPORTING V12 INDEPENDENT DESTRUCTIVE PASS:",len(cases))
