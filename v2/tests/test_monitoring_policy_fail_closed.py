#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]; CMD=["python3","v2/monitoring/verify_monitoring_policy.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
base=run(SRC)
if base.returncode: raise SystemExit("monitor baseline failed:\n"+base.stdout+base.stderr)
cases=[
 ("status-only",{"cycle_id":"bad1","policy_version":1,"started_at":"2026-09-29T00:00:00Z","outcome":"EXTERNAL_WAIT","commit_sha":None,"exception_reason":"STATUS_CHECK_ONLY","evidence":"none"},"invalid exception"),
 ("missing-reason",{"cycle_id":"bad2","policy_version":1,"started_at":"2026-09-29T00:00:00Z","outcome":"EXTERNAL_WAIT","commit_sha":None,"exception_reason":None,"evidence":"none"},"invalid exception"),
 ("commit-without-sha",{"cycle_id":"bad3","policy_version":1,"started_at":"2026-09-29T00:00:00Z","outcome":"COMMIT","commit_sha":None,"exception_reason":None,"evidence":"claimed"},"lacks 40-hex sha"),
]
for name,row,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  with (r/"v2/monitoring/cycles.jsonl").open("a") as f: f.write(json.dumps(row)+"\n")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(f"{name} was not rejected correctly:\n{out}")
  print("PASS expected monitoring rejection:",name)
print("PASS monitoring policy destructive cases rejected")
