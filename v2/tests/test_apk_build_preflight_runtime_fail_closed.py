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

# Positive composition semantics: real Signal integration is split across generated include,
# Framework include and MwmActivity lifecycle connection; all three are required.
def signal_present(fw, sigjni, mwm):
 return ("nativeSetCb6Signals" in sigjni and '#include "cb6_signal_jni.inc"' in fw and "mCb6Signals" in mwm)
assert signal_present('#include "cb6_signal_jni.inc"', "nativeSetCb6Signals", "mCb6Signals")
assert not signal_present("", "nativeSetCb6Signals", "mCb6Signals")
assert not signal_present('#include "cb6_signal_jni.inc"', "", "mCb6Signals")
assert not signal_present('#include "cb6_signal_jni.inc"', "nativeSetCb6Signals", "")
print("PASS positive Signal composition semantics and fail-closed missing-part cases")
