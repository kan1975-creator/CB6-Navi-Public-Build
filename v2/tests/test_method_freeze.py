#!/usr/bin/env python3
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
VERIFY=Path("v2/gates/verify_method_freeze.py")
cp=subprocess.run([sys.executable,str(SRC/VERIFY)],cwd=SRC,text=True,capture_output=True)
if cp.returncode: raise SystemExit("freeze baseline failed: "+cp.stdout+cp.stderr)
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(SRC,r)
 lock=json.loads((r/"v2/gates/method_freeze_lock.json").read_text())
 target=next(iter(lock["files"])); p=r/target; p.write_bytes(p.read_bytes()+b"\n")
 cp=subprocess.run([sys.executable,str(r/VERIFY)],cwd=r,text=True,capture_output=True)
 if cp.returncode==0 or "frozen method file changed" not in cp.stdout+cp.stderr: raise SystemExit("freeze destructive proof failed")
print("CB6 METHOD FREEZE SELFTEST PASS")
