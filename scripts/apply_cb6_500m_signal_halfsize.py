#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text(encoding="utf-8")

# Real-device correction after Run #51:
# cb6-signal-500 had no generated atlas resource, so z14 rendered nothing.
# Reuse the existing validated cb6-signal-s atlas symbol at z14 and z15.
# This keeps 500 m visible and makes the 200 m-class signal smaller too,
# without changing acquisition or the proven DebugMarkPoint rendering path.
old = 'symbols->insert({14, "cb6-signal"});'
old51 = 'symbols->insert({14, "cb6-signal-500"});\n        symbols->insert({15, "cb6-signal"});'
new = 'symbols->insert({14, "cb6-signal-s"});\n        symbols->insert({15, "cb6-signal-s"});'
if new not in s:
    if old51 in s:
        s = s.replace(old51, new, 1)
    elif old in s:
        s = s.replace(old, new, 1)
    else:
        raise SystemExit("z14 signal symbol anchor not found")
fw.write_text(s, encoding="utf-8")
print("CB6 wide/200m signal size applied with existing atlas symbol cb6-signal-s")
