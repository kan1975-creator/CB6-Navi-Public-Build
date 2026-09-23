#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
fw_path = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw_path.read_text(encoding="utf-8")

# Restore the exact render policy that was proven on-device in Run #133/#138.
# Keep the current Overpass/cache/JNI data path unchanged; only restore the
# DebugMarkPoint signal mark construction/render behavior.
typed_ctor = 'explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING) {}'
proven_ctor = 'explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt) {}'
if typed_ctor in s:
    s = s.replace(typed_ctor, proven_ctor, 1)
elif proven_ctor not in s:
    raise SystemExit("proven signal constructor anchor not found")

for line in (
    '      bool SymbolIsPOI() const override { return true; }\n',
    '      bool IsNonDisplaceable() const override { return true; }\n',
    '      bool GetDepthTestEnabled() const override { return false; }\n',
):
    s = s.replace(line, "")

# The proven signal mark belongs to DEBUG_MARK, so make that group explicitly visible.
if 'session.SetIsVisible(UserMark::Type::DEBUG_MARK, true);' not in s:
    raise SystemExit("DEBUG_MARK visibility missing")

required = (
    'class Cb6SignalMark final : public DebugMarkPoint',
    proven_ctor,
    'session.CreateUserMark<Cb6SignalMark>(pt);',
    'session.NotifyChanges();',
)
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("proven signal render requirements missing: " + ", ".join(missing))

fw_path.write_text(s, encoding="utf-8")
print("CB6 signal renderer restored to proven Run133/Run138 DebugMarkPoint path")
