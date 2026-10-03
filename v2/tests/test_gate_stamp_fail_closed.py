#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns(".git","out","comaps"))
 subprocess.run(["python3","v2/gates/create_gate_stamp.py"],cwd=root,check=True,capture_output=True,text=True)
 ok=subprocess.run(["python3","v2/gates/create_gate_stamp.py","--verify"],cwd=root,capture_output=True,text=True)
 if ok.returncode: raise SystemExit("GATE STAMP TEST FAIL baseline: "+ok.stdout+ok.stderr)
 p=root/"v2/gates/upstream_lock.json"; d=json.loads(p.read_text()); d["policy"]="changed-after-gate"; p.write_text(json.dumps(d))
 bad=subprocess.run(["python3","v2/gates/create_gate_stamp.py","--verify"],cwd=root,capture_output=True,text=True)
 out=bad.stdout+bad.stderr
 if bad.returncode==0 or "control file changed after gate: v2/gates/upstream_lock.json" not in out: raise SystemExit("GATE STAMP TEST FAIL mutation: "+out)
 print("PASS gate stamp rejects post-gate control mutation")
