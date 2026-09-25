#!/usr/bin/env python3
"""CB6 V2 baseline identity transform.

Responsibility: baseline/build/identity only.
This deliberately does not call any legacy CB6 cleanup, feature patch or audit.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
gradle = root / "android/app/build.gradle"
text = gradle.read_text(encoding="utf-8")

old_id = "project.ext.appId = 'app.comaps'"
new_id = "project.ext.appId = 'jp.cb6.navi'"
old_name = "project.ext.appName = 'CoMaps'"
new_name = "project.ext.appName = 'CB6 Navi'"

if old_id in text:
    text = text.replace(old_id, new_id, 1)
elif new_id not in text:
    raise SystemExit("V2 identity: appId anchor missing or unexpected")

if old_name in text:
    text = text.replace(old_name, new_name, 1)
elif new_name not in text:
    raise SystemExit("V2 identity: appName anchor missing or unexpected")

# V2 baseline release does not intentionally retain full native debug symbols in APK.
text = text.replace("    ndk.debugSymbolLevel = 'full'\n", "", 1)

gradle.write_text(text, encoding="utf-8")

# Scope guard: identity transform is intentionally tiny.
if "project.ext.appId = 'jp.cb6.navi'" not in text:
    raise SystemExit("V2 identity: package id was not applied")
if "project.ext.appName = 'CB6 Navi'" not in text:
    raise SystemExit("V2 identity: app name was not applied")

print("CB6 V2 minimal identity applied: jp.cb6.navi / CB6 Navi")
