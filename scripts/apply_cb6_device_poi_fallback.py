#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "comaps")

# This patch is deliberately bounded to two known files; do not recursively scan
# the CoMaps tree. Restore the exact DebugMarkPoint signal render behavior proven
# on the real device while keeping current Overpass/cache/JNI data logic intact.
fw_path = root / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw_path.read_text(encoding="utf-8")
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
required = (
    'class Cb6SignalMark final : public DebugMarkPoint',
    proven_ctor,
    'session.SetIsVisible(UserMark::Type::DEBUG_MARK, true);',
    'session.CreateUserMark<Cb6SignalMark>(pt);',
    'session.NotifyChanges();',
)
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("proven signal render requirements missing: " + ", ".join(missing))
fw_path.write_text(s, encoding="utf-8")
print("restored proven Run133/Run138 DebugMarkPoint signal renderer")

# Secondary real-device fallback: allow downloaded CoMaps map data to render
# traffic signals if the supplemental network/JNI path has no data.
for style in ("vehicle", "default"):
    p = root / "data/styles" / style / "include" / "Icons.mapcss"
    if not p.exists():
        continue
    css = p.read_text(encoding="utf-8")
    marker = "/* CB6 real-device critical POI fallback */"
    if marker not in css:
        css += "\n\n" + marker + "\n"
        css += "node|z15-[highway=traffic_signals] { icon-image: traffic_signals.svg; }\n"
        p.write_text(css, encoding="utf-8")
    print("enabled downloaded-map traffic signal fallback:", p)
