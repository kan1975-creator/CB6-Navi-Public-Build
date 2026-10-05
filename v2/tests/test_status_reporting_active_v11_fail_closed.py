#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_active_v11.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v11 baseline failed")
cases=[
 ("disable-push",lambda q:q["freshness_rule"]["unknown_run_id_discovery"].update({"discovery_must_include_push_triggered_runs":False}),"unknown-run discovery guard invalid"),
 ("drop-head-bind",lambda q:q["freshness_rule"]["unknown_run_id_discovery"].update({"discovered_run_must_match_current_head_sha":False}),"unknown-run discovery guard invalid"),
 ("allow-zero-absence",lambda q:q["freshness_rule"]["unknown_run_id_discovery"].update({"zero_results_from_incomplete_discovery_is_not_run_nonexistence_evidence":False}),"unknown-run discovery guard invalid"),
 ("pending-adoption",lambda q:q["adoption"].update({"status":"NOT_ADOPTED"}),"v11 lifecycle not finalized"),
]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps")); p=r/"v2/gates/status_reporting_contract_v11.json"; q=json.loads(p.read_text()); mut(q); p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected active v11 rejection:",name)
print("PASS status reporting active v11 destructive cases rejected")
