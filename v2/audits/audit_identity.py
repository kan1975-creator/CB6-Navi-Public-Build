#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
gradle = (root / "android/app/build.gradle").read_text(encoding="utf-8")
required = [
    "project.ext.appId = 'jp.cb6.navi'",
    "project.ext.appName = 'CB6 Navi'",
]
for token in required:
    if token not in gradle:
        raise SystemExit(f"V2 identity audit failed: missing {token}")
for forbidden in [
    "project.ext.appId = 'app.comaps'",
    "project.ext.appName = 'CoMaps'",
]:
    if forbidden in gradle:
        raise SystemExit(f"V2 identity audit failed: stale {forbidden}")
print("CB6 V2 identity audit OK")
