#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text(encoding="utf-8")

# Real-device refinement after Run #45:
# 500 m signals were visible but visually too large. Keep the proven renderer,
# acquisition and 200 m/forward behavior unchanged; use a dedicated half-size
# symbol only at z14, then return to the existing normal symbol from z15.
old = 'symbols->insert({14, "cb6-signal"});'
new = 'symbols->insert({14, "cb6-signal-500"});\n        symbols->insert({15, "cb6-signal"});'
if new not in s:
    if old not in s:
        raise SystemExit("z14 signal symbol anchor not found")
    s = s.replace(old, new, 1)
fw.write_text(s, encoding="utf-8")
print("CB6 500m signal half-size selector applied; z15+ proven sizes preserved")
