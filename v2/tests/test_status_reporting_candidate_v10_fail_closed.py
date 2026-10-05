#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v10.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v10 baseline failed")
cases=[
 ("disable-direct-refresh",lambda q:q["freshness_rule"]["known_run_id_direct_refresh"].update({"required_when_tracking_run_id_known":False}),"known-run direct-refresh guard invalid"),
 ("make-list-primary",lambda q:q["freshness_rule"]["known_run_id_direct_refresh"].update({"run_list_is_supplementary":False}),"known-run direct-refresh guard invalid"),
 ("allow-list-absence-state-change",lambda q:q["freshness_rule"]["known_run_id_direct_refresh"].update({"absence_from_run_list_is_not_state_change_evidence":False}),"known-run direct-refresh guard invalid"),
 ("allow-failed-inference",lambda q:q["freshness_rule"]["known_run_id_direct_refresh"]["forbidden_inferences_from_list_absence"].remove("run_failed"),"forbidden list-absence inference missing"),
]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_candidate_v10.json"; q=json.loads(p.read_text()); mut(q); p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected known-run refresh rejection:",name)
print("PASS status reporting v10 known-run direct-refresh destructive cases rejected")
