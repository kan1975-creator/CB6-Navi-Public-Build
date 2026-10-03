#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
VERIFY=["python3","v2/gates/verify_method_version_coverage.py"]
def run(root):
 return subprocess.run(VERIFY,cwd=root,text=True,capture_output=True)
ok=run(SRC)
if ok.returncode: raise SystemExit("METHOD VERSION TEST baseline failed:\n"+ok.stdout+ok.stderr)
cases=[]
def mutate_old(root):
 p=root/"v2/gates/features/signals.json"; d=json.loads(p.read_text()); d["method_version"]=1; p.write_text(json.dumps(d))
cases.append(("one-feature-old",mutate_old,"signals.json method_version=1"))
def mutate_missing(root):
 p=root/"v2/gates/features/convenience-brands.json"; d=json.loads(p.read_text()); d.pop("method_version",None); p.write_text(json.dumps(d))
cases.append(("field-missing",mutate_missing,"convenience-brands.json method_version=None"))
def mutate_new(root):
 p=root/"v2/gates/features/future-feature.json"; p.write_text(json.dumps({"schema":1,"feature_id":"future-feature"}))
cases.append(("new-feature-unversioned",mutate_new,"future-feature.json method_version=None"))
for name,mutate,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns(".git","out","comaps"))
  mutate(root); cp=run(root); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(f"METHOD VERSION TEST FAIL {name}: rc={cp.returncode}\n{out}")
  print("PASS expected method-version rejection:",name)
print("PASS method-version coverage destructive cases rejected")
