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
# Create a dedicated narrower/smaller z14 resource from the validated small icon.
# z15+ continues to use cb6-signal-s unchanged.
for theme in ("light", "dark"):
    dst = ROOT / "data/styles/default" / theme / "symbols" / "cb6-signal-xs.svg"
    dst.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="8" height="14" viewBox="0 0 8 14"><rect x="1" y="1" width="6" height="11" rx="2" fill="#202020" stroke="#FFFFFF" stroke-width="0.7"/><circle cx="4" cy="3.4" r="1.35" fill="#EF5350"/><circle cx="4" cy="6.5" r="1.35" fill="#FFCA28"/><circle cx="4" cy="9.6" r="1.35" fill="#43A047"/><rect x="3.55" y="12" width="0.9" height="2" fill="#555555"/></svg>', encoding="utf-8")
print("CB6 500m extra-small/narrow signal applied; 200m cb6-signal-s preserved")
