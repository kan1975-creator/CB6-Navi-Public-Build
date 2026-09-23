#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "comaps")

# Real-device fallback: keep the CB6 supplemental renderer, but also allow
# downloaded CoMaps map data to render critical driving POIs when Overpass/JNI
# supplementation is unavailable.
for style in ("vehicle", "default"):
    p = root / "data/styles" / style / "include" / "Icons.mapcss"
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    marker = "/* CB6 real-device critical POI fallback */"
    if marker in s:
        continue
    s += "\n\n" + marker + "\n"
    s += "node|z15-[highway=traffic_signals] { icon-image: traffic_signals.svg; }\n"
    p.write_text(s, encoding="utf-8")
    print("enabled downloaded-map traffic signal fallback:", p)
