#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()


def read(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("missing: " + rel)
    return p.read_text(encoding="utf-8")


def write(rel, s):
    p = ROOT / rel
    p.write_text(s, encoding="utf-8")
    print("v1.4 patched:", rel)


# 1) Real-device scale calibration.
# The CB6 screenshot labelled 500 m is still inside CoMaps' z17 detail range.
# Keep small suburb/locality/quarter/neighbourhood captions hidden through z17,
# then allow them from z18+ (approximately the desired 100 m detail range on CB6).
label_count = 0
for p in sorted((ROOT / "data/styles").glob("*/include/Basemap_label.mapcss")):
    s = p.read_text(encoding="utf-8")
    s = s.replace("z10-16[place=suburb]", "z10-17[place=suburb]")
    s = s.replace("z12-16[place=locality]", "z12-17[place=locality]")
    s = s.replace("z12-16[place=quarter]", "z12-17[place=quarter]")
    s = s.replace("z12-16[place=neighbourhood]", "z12-17[place=neighbourhood]")
    s = s.replace("z13-16[place=suburb]", "z13-17[place=suburb]")
    s = s.replace("z13-16[place=locality]", "z13-17[place=locality]")
    s = s.replace("z13-16[place=quarter]", "z13-17[place=quarter]")
    s = s.replace("z13-16[place=neighbourhood]", "z13-17[place=neighbourhood]")
    p.write_text(s, encoding="utf-8")
    label_count += 1
    print("v1.4 label scale:", p.relative_to(ROOT))
if label_count < 3:
    raise SystemExit(f"unexpected label style count: {label_count}")

# 2) Make the OFFLINE/native CoMaps features visible instead of relying only on
# the Overpass supplement. The map data already contains shop=convenience and
# highway=traffic_signals. Raise convenience visibility to z12 and keep signals z12.
icon_count = 0
conv_count = 0
signal_count = 0
for p in sorted((ROOT / "data/styles").glob("*/include/Icons.mapcss")):
    s = p.read_text(encoding="utf-8")
    before = s
    # Existing CoMaps styles use z16/z17 (and occasionally later) for convenience.
    s, nconv = re.subn(r"node\|z1[6-9]-\[shop=convenience\]", "node|z12-[shop=convenience]", s)
    # Keep the CB6 fallback at z12 even if an older selector survived in a style.
    s, nsig = re.subn(r"node\|z(?:1[3-9]|2[0-9])-\[highway=traffic_signals\]",
                      "node|z12-[highway=traffic_signals]", s)
    p.write_text(s, encoding="utf-8")
    icon_count += 1
    conv_count += nconv
    signal_count += nsig
    if s != before:
        print("v1.4 native POI style:", p.relative_to(ROOT))
if icon_count < 3:
    raise SystemExit(f"unexpected icon style count: {icon_count}")
if conv_count < 1:
    raise SystemExit("no native convenience selector was widened")

# 3) CoMaps overlay priority files can contain generated commented placeholders.
# A MapCSS selector without an active overlay priority can compile but never displace
# other overlays on the real device. Activate convenience + traffic signals only in
# root priority files (default and vehicle-like standalone files); imported child
# files keep their placeholders commented to avoid duplicate priorities.
prio_roots = 0
for p in sorted((ROOT / "data/styles").glob("*/include/priorities_4_overlays.prio.txt")):
    s = p.read_text(encoding="utf-8")
    if '@import(' in s:
        continue
    prio_roots += 1
    lines = s.splitlines()
    changed = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        prefix = line[:len(line)-len(stripped)]
        if stripped.startswith("# shop-convenience"):
            lines[i] = prefix + stripped[2:] if stripped.startswith("# ") else prefix + stripped[1:]
            changed = True
        elif stripped.startswith("# highway-traffic_signals"):
            lines[i] = prefix + stripped[2:] if stripped.startswith("# ") else prefix + stripped[1:]
            changed = True
    if changed:
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("v1.4 priority activated:", p.relative_to(ROOT))
if prio_roots < 2:
    raise SystemExit(f"unexpected standalone priority count: {prio_roots}")

# 4) Road-name HUD: 35 m was too strict for real CB6 GPS/map geometry.
# Search the nearest named highway within 90 m, while retaining the existing
# reverse-geocoder street fallback when no named road is found.
rel = "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = read(rel)
old = "}, point, 35.0 /* toleranceInMeters */);"
new = "}, point, 90.0 /* toleranceInMeters: CB6 real-device GPS/map offset */);"
if old not in s and new not in s:
    raise SystemExit("nearest-road tolerance anchor missing")
if old in s:
    s = s.replace(old, new, 1)
write(rel, s)

print(f"CB6 Navi v1.4 real-device fixes applied: {label_count} label styles, {icon_count} icon styles, {prio_roots} root priority files.")
