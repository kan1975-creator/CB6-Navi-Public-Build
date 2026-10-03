#!/usr/bin/env python3
"""Destructive proof that preflight_gate1.py detects generated-source drift."""
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path
P=argparse.ArgumentParser(); P.add_argument("transformed_root",type=Path); P.add_argument("manifest",type=Path); a=P.parse_args()
ROOT=Path(__file__).resolve().parents[2]; AUDIT=ROOT/"v2/audits/preflight_gate1.py"
base=a.transformed_root.resolve(); manifest=a.manifest.resolve()
cp=subprocess.run(["python3",str(AUDIT),str(base),str(manifest),"--verify"],cwd=ROOT,text=True,capture_output=True)
if cp.returncode!=0: raise SystemExit("PREFLIGHT SELFTEST BASELINE FAIL:\n"+cp.stdout+cp.stderr)
with tempfile.TemporaryDirectory() as td:
 mutant=Path(td)/"comaps"; shutil.copytree(base,mutant,symlinks=True)
 tracked=json.loads(manifest.read_text())
 rel=next(iter(sorted(tracked)))
 p=mutant/rel
 if not p.is_file(): raise SystemExit("PREFLIGHT SELFTEST FIXTURE MISSING: "+rel)
 with p.open("ab") as fh: fh.write(b"\n// cb6 destructive preflight mutation\n")
 bad=subprocess.run(["python3",str(AUDIT),str(mutant),str(manifest),"--verify"],cwd=ROOT,text=True,capture_output=True)
 out=bad.stdout+bad.stderr
 if bad.returncode==0 or "Post-configure source changed:" not in out:
  raise SystemExit("PREFLIGHT SELFTEST FAIL: mutation accepted\n"+out)
 print("PASS expected preflight rejection: generated-source drift ->",rel)
print("CB6 PREFLIGHT AUDIT SELFTEST PASS: baseline accepted and generated-source mutation rejected")
