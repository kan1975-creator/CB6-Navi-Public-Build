#!/usr/bin/env python3
"""Destructive proof that audit_signals.py rejects broken transformed Signal source."""
import argparse, shutil, subprocess, tempfile
from pathlib import Path

P=argparse.ArgumentParser()
P.add_argument("transformed_root",type=Path)
a=P.parse_args()
ROOT=Path(__file__).resolve().parents[2]
AUDIT=ROOT/"v2/audits/audit_signals.py"

def run(root):
 return subprocess.run(["python3",str(AUDIT),str(root)],cwd=ROOT,text=True,capture_output=True)

base=a.transformed_root.resolve()
ok=run(base)
if ok.returncode!=0:
 raise SystemExit("SIGNAL AUDIT SELFTEST BASELINE FAIL:\n"+ok.stdout+ok.stderr)

cases=[
 ("publisher-group", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "ClearGroup(UserMark::Type::CB6_SIGNAL)", "ClearGroup(UserMark::Type::DEBUG_MARK)", "publisher clears unrelated state"),
 ("symbol-zoom", "libs/map/cb6_signal_mark.hpp",
  'return 12;', 'return 11;', "minimum zoom mismatch"),
 ("acquisition-query", "android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java",
  "[highway=traffic_signals]", "[highway=traffic_lights]", "current-spec query highway=traffic_signals"),
]
for name,rel,old,new,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  mutant=Path(td)/"comaps"
  shutil.copytree(base,mutant,symlinks=True)
  p=mutant/rel
  s=p.read_text()
  if old not in s: raise SystemExit(f"SELFTEST FIXTURE ANCHOR MISSING {name}: {old}")
  p.write_text(s.replace(old,new,1))
  cp=run(mutant)
  out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out:
   raise SystemExit(f"SIGNAL AUDIT SELFTEST FAIL {name}: rc={cp.returncode}\n{out}")
  print("PASS expected signal audit rejection:",name,"->",needle)
print("CB6 SIGNAL AUDIT SELFTEST PASS: baseline accepted and destructive mutations rejected")
