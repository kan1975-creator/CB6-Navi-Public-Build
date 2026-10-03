#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v7.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v7 candidate baseline failed")
cases=[
 ("fixed-threshold",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"fixed_or_unsubstantiated_threshold_forbidden":False}),"normal duration guard invalid"),
 ("wrong-basis",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"basis":"FIXED_MINUTES"}),"normal duration evidence basis missing"),
 ("allow-early-overrun",lambda d:d["rules"]["待ち"]["wait_time_display"]["exceeded_normal_duration"].update({"may_classify_exceeded_only_after_evidence_based_normal_duration_range_exceeded":False}),"normal duration guard invalid"),
 ("change-v6-display",lambda d:d["final_summary_display"].update({"duplicate_information_forbidden":False}),"existing v6 contract changed"),
 ("self-activate",lambda d:d.update({"status":"ACTIVE"}),"candidate v7 identity/status invalid")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_candidate_v7.json"; q=json.loads(p.read_text()); mut(q); p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v7 rejection:",name)
print("PASS status reporting v7 normal-duration destructive cases rejected")
