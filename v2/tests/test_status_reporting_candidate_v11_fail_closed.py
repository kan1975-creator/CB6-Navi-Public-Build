#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v11.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v11 candidate baseline failed")
cases=[
 ("disable-push-discovery",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"discovery_must_include_push_triggered_runs":False}),"unknown-run discovery guard invalid"),
 ("accept-pr-only",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"pull_request_only_run_lookup_is_insufficient_for_push_discovery":False}),"unknown-run discovery guard invalid"),
 ("allow-incomplete-zero",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"zero_results_from_incomplete_discovery_is_not_run_nonexistence_evidence":False}),"unknown-run discovery guard invalid"),
 ("drop-head-match",lambda d:d["freshness_rule"]["unknown_run_id_discovery"].update({"discovered_run_must_match_current_head_sha":False}),"unknown-run discovery guard invalid"),
 ("self-active",lambda d:d.update({"status":"ACTIVE"}),"v11 candidate identity/status invalid"),
 ("skip-independent",lambda d:d["adoption"]["required_before_active"].remove("independent_review"),"activation prerequisite missing"),
]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_v11_candidate.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected v11 candidate rejection:",name)
print("PASS status reporting v11 candidate destructive cases rejected")
