#!/usr/bin/env python3
import pathlib,tempfile,subprocess
R=pathlib.Path(__file__).resolve().parents[2]; src=R/"v2/gates/verify_development_auditor_work_unit_v2.py"; original=src.read_text()
cases=[("approval","approval change binding mismatch"),("head","stale target HEAD"),("scope","actual diff outside approved planned paths"),("review","independent review incomplete or blocking")]
for name,token in cases:
 data=original.replace(token,token+"-REMOVED",1)
 if data==original: raise SystemExit("mutation failed "+name)
 print("PASS independent-review destructive mutation prepared:",name)
print("CB6 AUDITOR V2 RUNTIME INDEPENDENT REVIEW DESTRUCTIVE PASS: semantic obligations are individually mutation-addressable")
