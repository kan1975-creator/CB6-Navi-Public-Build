#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_v7_independent_review.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v7 independent review baseline failed")
cases=[
 ("fixed-threshold","v2/gates/status_reporting_contract_candidate_v7.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"fixed_or_unsubstantiated_threshold_forbidden":False}),"v7 normal duration guard invalid"),
 ("wrong-basis","v2/gates/status_reporting_contract_candidate_v7.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"basis":"FIXED_MINUTES"}),"v7 normal duration evidence basis missing"),
 ("allow-early-overrun","v2/gates/status_reporting_contract_candidate_v7.json",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"may_classify_exceeded_only_after_evidence_based_normal_duration_range_exceeded":False}),"v7 normal duration guard invalid"),
 ("change-v6-display","v2/gates/status_reporting_contract_candidate_v7.json",lambda d:d["final_summary_display"].update({"duplicate_information_forbidden":False}),"ACTIVE v6 contract changed in candidate"),
 ("self-active","v2/gates/status_reporting_contract_candidate_v7.json",lambda d:d.update({"status":"ACTIVE"}),"v7 candidate identity/status invalid"),
 ("active-v6-demoted","v2/gates/status_reporting_contract_v6.json",lambda d:d.update({"status":"CANDIDATE"}),"ACTIVE v6 authority changed")]
for name,path,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/path; d=json.loads(p.read_text(encoding="utf-8")); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v7-review rejection:",name)
print("PASS status reporting v7 independent-review destructive cases rejected")
