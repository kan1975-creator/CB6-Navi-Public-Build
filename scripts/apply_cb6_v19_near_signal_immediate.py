#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
s = mgr.read_text(encoding="utf-8")

# Keep the validated v1.8 signal renderer/policy unchanged. The signal-only
# Overpass request already completes before the optional POI request, but v1.6
# waited for the POI enrichment before sending those fresh signals to JNI. On a
# slow/failed POI endpoint that can delay current nearby signals for tens of
# seconds. Publish the fresh signal set immediately, then enrich and publish the
# merged set as before.
anchor = '''    Points merged = signals.copy();
    String poiQuery = buildPoiQuery(lat, lon);'''
replacement = '''    // Nearby/current signals are the time-critical layer. Publish them as soon as
    // the dedicated signal request succeeds; optional POI enrichment must never
    // delay physical traffic-signal visibility.
    postPoints(signals, "NET-SIG");

    Points merged = signals.copy();
    String poiQuery = buildPoiQuery(lat, lon);'''

if 'postPoints(signals, "NET-SIG");' not in s:
    if anchor not in s:
        raise SystemExit("v1.9 immediate-signal insertion point not found")
    s = s.replace(anchor, replacement, 1)

if s.count('postPoints(signals, "NET-SIG");') != 1:
    raise SystemExit("v1.9 immediate-signal publish duplicated")
if s.index('postPoints(signals, "NET-SIG");') > s.index('String poiQuery = buildPoiQuery(lat, lon);'):
    raise SystemExit("v1.9 signal publish must precede optional POI request")

# Guard all validated v1.8 behavior against accidental changes in this patch.
required = (
    'KIND_SIGNAL_FORWARD = 22',
    'FORWARD_SIGNAL_MAX_M = 450.0f',
    'FORWARD_CONE_DEG = 45.0f',
    'parseSignalsNearFirst',
    'MAX_SIGNAL_POINTS = 1400',
    'Framework.nativeSetCb6DrivingMarks(points.lats(), points.lons(), kindsForCurrentDirection(points));',
)
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("v1.9 would run without required v1.8 manager policy: " + ", ".join(missing))

mgr.write_text(s, encoding="utf-8")
print("CB6 v1.9 applied: fresh traffic signals publish immediately before optional POI enrichment")
