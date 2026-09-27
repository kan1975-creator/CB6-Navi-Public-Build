#!/usr/bin/env python3
"""Root-level proof that an unknown/unmapped repository change is detected.

This proof is intentionally independent of the development-method freeze. Root
certification must be able to prove unknown-change fail-closed behavior before
a new method freeze is certified.
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
VERIFY=Path("v2/gates/verify_root_invariants.py")
base=subprocess.run([sys.executable,str(SRC/VERIFY)],cwd=SRC,text=True,capture_output=True)
if base.returncode:
 raise SystemExit("unknown-change root baseline failed: "+base.stdout+base.stderr)
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns(".git","out","comaps"))
 p=root/"v2/gates/repository_state_manifest.json"; d=json.loads(p.read_text())
 d["outputs"]["unexpected_unmapped_state"]=["v2/gates/project_state.json"]
 p.write_text(json.dumps(d))
 cp=subprocess.run([sys.executable,str(root/VERIFY)],cwd=root,text=True,capture_output=True)
 if cp.returncode==0 or "reconstruction outputs mismatch" not in cp.stdout+cp.stderr:
  raise SystemExit("unknown-change root destructive proof failed: "+cp.stdout+cp.stderr)
print("CB6 ROOT UNKNOWN CHANGE SELFTEST PASS")
