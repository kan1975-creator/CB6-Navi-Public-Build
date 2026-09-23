#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
s = mgr.read_text(encoding="utf-8")

# Keep the proven Run30 renderer untouched. Improve only acquisition/refresh of
# nearby OSM traffic-signal nodes so close intersections are less likely to be
# missing on the real device.
replacements = (
    ('private static final long NEAR_REFRESH_MS = 90 * 1000L;', 'private static final long NEAR_REFRESH_MS = 45 * 1000L;'),
    ('private static final long NEAR_RETRY_MS = 20 * 1000L;', 'private static final long NEAR_RETRY_MS = 12 * 1000L;'),
    ('private static final float NEAR_REFRESH_DISTANCE_M = 500.0f;', 'private static final float NEAR_REFRESH_DISTANCE_M = 250.0f;'),
    ('private static final int NEAR_SIGNAL_RADIUS_M = 2000;', 'private static final int NEAR_SIGNAL_RADIUS_M = 3000;'),
)
for old, new in replacements:
    if new not in s:
        if old not in s:
            raise SystemExit('near-signal constant anchor not found: ' + old)
        s = s.replace(old, new, 1)

# Keep the existing proven Overpass query syntax. Coverage is improved by radius,
# cadence and movement threshold only; do not alter rendering or parser behavior.
required = (
    'NEAR_REFRESH_MS = 45 * 1000L',
    'NEAR_RETRY_MS = 12 * 1000L',
    'NEAR_REFRESH_DISTANCE_M = 250.0f',
    'NEAR_SIGNAL_RADIUS_M = 3000',
    '[highway=traffic_signals]',
    'postNearbySignals(nearby, lat, lon);',
)
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit('near-signal coverage patch missing: ' + ', '.join(missing))

mgr.write_text(s, encoding='utf-8')
print('CB6 near-signal coverage applied: 3km / 45s / 250m refresh, proven renderer unchanged')
