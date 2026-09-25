#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path("comaps").resolve()
mgr=(ROOT/"android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java").read_text(encoding="utf-8")
errors=[]
def need(t,label):
    if t not in mgr: errors.append("missing "+label+": "+t)
for t,l in (
 ("mConvenienceExecutor = Executors.newSingleThreadExecutor()","independent executor"),
 ("requestConvenienceIfNeeded(lat, lon, now);","independent scheduler"),
 ("CONVENIENCE_REFRESH_MS = 3 * 60 * 1000L","store refresh cadence"),
 ("CONVENIENCE_REFRESH_DISTANCE_M = 800.0f","store movement refresh"),
 ("private void refreshConvenience(double lat, double lon)","store fetch method"),
 ("String query = buildConvenienceQuery(lat, lon);","store-only query"),
 ("private void postIndependentConvenience(@NonNull Points stores)","store merge publisher"),
 ("isConvenienceKind(kind)","store replacement filter"),
 ("CB6-CONVENIENCE fetched=","fetch diagnostic"),
 ("CB6-CONVENIENCE JNI stores=","JNI diagnostic"),
 ("CB6-CONVENIENCE PROBE posted about 120m east","real-device render probe"),
 ("NEAR_REFRESH_MS = 45 * 1000L","frozen signal refresh"),
 ("NEAR_SIGNAL_RADIUS_M = 3000","frozen signal radius"),
): need(t,l)
# The dedicated store request must be scheduled before the broad 10-minute early-return.
if "requestConvenienceIfNeeded(lat, lon, now);" in mgr and "if (now - mLastRequestTime < REFRESH_MS" in mgr:
    if mgr.index("requestConvenienceIfNeeded(lat, lon, now);") > mgr.index("if (now - mLastRequestTime < REFRESH_MS"):
        errors.append("convenience scheduler is incorrectly gated by broad refresh")
if errors:
    print("CB6 CONVENIENCE AUDIT FAILED")
    [print(" -",e) for e in errors]
    raise SystemExit(1)
print("CB6 CONVENIENCE AUDIT OK: independent acquisition, retained merge, diagnostics, frozen signal policy")
