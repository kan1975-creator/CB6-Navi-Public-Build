#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
cmd=["python3","v2/gates/verify_acceptance_contract.py","convenience-brands"]
ok=subprocess.run(cmd,cwd=SRC,text=True,capture_output=True)
if ok.returncode: raise SystemExit("acceptance baseline failed: "+ok.stdout+ok.stderr)
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(SRC,r,ignore=shutil.ignore_patterns("out","comaps"))
 p=r/"v2/gates/acceptance/convenience-brands/v1.json"; d=json.loads(p.read_text()); d["criteria"][0]["observable"]="weakened after implementation"; p.write_text(json.dumps(d))
 bad=subprocess.run(cmd,cwd=r,text=True,capture_output=True); out=bad.stdout+bad.stderr
 if bad.returncode==0 or "changed in place" not in out: raise SystemExit("acceptance mutation was not rejected: "+out)
print("PASS sealed acceptance criteria reject in-place mutation")
