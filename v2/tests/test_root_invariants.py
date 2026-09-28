#!/usr/bin/env python3
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
VERIFY=Path("v2/gates/verify_root_invariants.py")
def run(root):
    return subprocess.run([sys.executable,str(root/VERIFY)],cwd=root,text=True,capture_output=True)
base=run(SRC)
if base.returncode:
    raise SystemExit("root invariant baseline failed: "+base.stdout+base.stderr)
with tempfile.TemporaryDirectory() as td:
    r=Path(td)/"repo"; shutil.copytree(SRC,r)
    p=r/"v2/gates/repository_state_manifest.json"; d=json.loads(p.read_text()); d["outputs"].pop("known_failures"); p.write_text(json.dumps(d))
    cp=run(r)
    if cp.returncode==0 or "reconstruction outputs mismatch" not in cp.stdout+cp.stderr:
        raise SystemExit("context-loss destructive proof failed")
with tempfile.TemporaryDirectory() as td:
    r=Path(td)/"repo"; shutil.copytree(SRC,r)
    (r/"v2/gates/active_decisions.json").unlink()
    cp=run(r)
    if cp.returncode==0 or "reconstruction path missing" not in cp.stdout+cp.stderr:
        raise SystemExit("missing-state destructive proof failed")
print("CB6 ROOT INVARIANT SELFTEST PASS")

# Root certification itself must fail closed: changing only a feature-execution
# permission must never be enough to authorize lower-layer work.
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(SRC,r)
 root_path=r/"v2/gates/root_invariants.json"
 root=json.loads(root_path.read_text())
 root["certification"]["status"]="UNDER_CONSTRUCTION"
 root["certification"]["feature_execution_permitted"]=True
 root_path.write_text(json.dumps(root))
 cp=subprocess.run([sys.executable,str(r/VERIFY)],cwd=r,text=True,capture_output=True)
 if cp.returncode==0 or "lower layers must be blocked" not in cp.stdout+cp.stderr:
  raise SystemExit("root certification permission destructive proof failed")

# A CERTIFIED label without the complete proof set must never open the root.
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(SRC,r)
 root_path=r/"v2/gates/root_invariants.json"
 root=json.loads(root_path.read_text())
 root["certification"]={"status":"CERTIFIED","feature_execution_permitted":True,"proof":{}}
 root_path.write_text(json.dumps(root))
 cp=run(r)
 if cp.returncode==0 or "root certification proof incomplete" not in cp.stdout+cp.stderr:
  raise SystemExit("self-asserted root certification destructive proof failed")
