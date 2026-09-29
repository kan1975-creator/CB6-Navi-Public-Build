#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_monitoring_policy.py"]
def check(root): return subprocess.run(CMD,cwd=root,text=True,capture_output=True)
if check(SRC).returncode: raise SystemExit("monitoring baseline failed")
cases=[
 ("no-commit-no-exception",{"schema":1,"method_version":2,"cycle_id":"x","started_at":"2026-09-29T00:00:00Z","basis_head":"a"*40,"outcome":"EXCEPTION","commit_sha":None,"exception":None,"evidence":""},"invalid/missing exception"),
 ("invalid-exception",{"schema":1,"method_version":2,"cycle_id":"x","started_at":"2026-09-29T00:00:00Z","basis_head":"a"*40,"outcome":"EXCEPTION","commit_sha":None,"exception":"STATUS_ONLY","evidence":"checked status"},"invalid/missing exception"),
 ("commit-without-sha",{"schema":1,"method_version":2,"cycle_id":"x","started_at":"2026-09-29T00:00:00Z","basis_head":"a"*40,"outcome":"COMMIT","commit_sha":"","exception":None,"evidence":"claimed work"},"COMMIT lacks valid commit_sha")
]
for name,row,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  d=r/"v2/gates/monitoring/cycles"; d.mkdir(parents=True,exist_ok=True); (d/"destructive.json").write_text(json.dumps(row))
  cp=check(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" was not rejected correctly:\n"+out)
  print("PASS expected monitoring rejection:",name)
print("PASS monitoring policy destructive cases rejected")
