#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
path = root / "data/styles/vehicle/include/priorities_4_overlays.prio.txt"
lines = path.read_text(encoding="utf-8").splitlines()

# CB6 adds a traffic-signal icon rule to the vehicle style. The pinned CoMaps
# vehicle priority file has no traffic-signal selector at all, so add a dedicated
# priority group. generate_drules.sh will reformat/re-sort the file later.
if not any("highway-traffic_signals" in line for line in lines):
    lines.extend([
        "",
        "highway-traffic_signals                             # CB6 icon z19-",
        "=== 215",
    ])

# The CB6 style suppresses locality int_name, but the drawing-rule compiler still
# requires that selector to have an overlay priority. Give it locality's priority.
if not any("place-locality::int_name" in line for line in lines):
    locality_indexes = [
        i for i, line in enumerate(lines)
        if line.strip().split("#", 1)[0].strip() == "place-locality"
    ]
    if len(locality_indexes) != 1:
        raise SystemExit(f"place-locality selector: expected 1 match, got {len(locality_indexes)}")
    li = locality_indexes[0]
    priority_index = None
    for j in range(li + 1, min(len(lines), li + 25)):
        s = lines[j].strip()
        if s.startswith("==="):
            if s != "=== 1850":
                raise SystemExit(f"place-locality priority: expected 1850, got {lines[j]!r}")
            priority_index = j
            break
    if priority_index is None:
        nearby = lines[li : min(len(lines), li + 25)]
        raise SystemExit(f"place-locality priority 1850 not found: {nearby!r}")
    lines.insert(
        priority_index,
        "place-locality::int_name                            # CB6 same priority as locality",
    )

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("patched:", path.relative_to(root))
print("CB6 vehicle priorities added: traffic signals=215, locality int_name=1850")
