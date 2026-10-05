#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_v11_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("v11 independent baseline failed")
cases=[
 ("disable-push",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"discovery_must_include_push_triggered_runs":False}),"unknown-run independent guard invalid"),
 ("allow-pr-only",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"pull_request_only_run_lookup_is_insufficient_for_push_discovery":False}),"unknown-run independent guard invalid"),
 ("drop-head-bind",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"discovered_run_must_match_current_head_sha":False}),"unknown-run independent guard invalid"),
 ("allow-zero-absence",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"zero_results_from_incomplete_discovery_is_not_run_nonexistence_evidence":False}),"unknown-run independent guard invalid"),
]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_v11_candidate.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected v11 independent rejection:",name)
print("PASS v11 independent destructive cases rejected")
