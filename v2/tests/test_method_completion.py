#!/usr/bin/env python3
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
VERIFY=Path("v2/gates/verify_method_completion.py")
cp=subprocess.run([sys.executable,str(SRC/VERIFY)],cwd=SRC,text=True,capture_output=True)
if cp.returncode: raise SystemExit("completion baseline failed: "+cp.stdout+cp.stderr)
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(SRC,r)
 p=r/"v2/gates/development_method_completion.json"; d=json.loads(p.read_text()); d["proof"]["zero_omission"]=False; p.write_text(json.dumps(d,indent=2)+"\n")
 cp=subprocess.run([sys.executable,str(r/VERIFY)],cwd=r,text=True,capture_output=True)
 if cp.returncode==0 or "completion proof incomplete" not in cp.stdout+cp.stderr: raise SystemExit("completion destructive proof failed")
print("CB6 METHOD COMPLETION SELFTEST PASS")
