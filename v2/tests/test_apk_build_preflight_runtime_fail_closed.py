#!/usr/bin/env python3
import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"gates/verify_apk_build_preflight_runtime.py"
spec=importlib.util.spec_from_file_location("preflight",P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
base={k:True for k in m.REQS}
m.validate_state(base)
for key in m.REQS:
 d=dict(base); d[key]=False
 try: m.validate_state(d)
 except ValueError as e:
  if key not in str(e): raise SystemExit("wrong rejection for "+key)
 else: raise SystemExit("missing fail-closed rejection for "+key)
 print("PASS expected executable preflight rejection:",key)
print("PASS executable APK build preflight destructive cases rejected")
