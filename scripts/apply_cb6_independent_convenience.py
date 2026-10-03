#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
s = mgr.read_text(encoding="utf-8")

# CB6 convenience stores are intentionally independent of the traffic-signal
# scheduler. A failed/slow signal request must never prevent store acquisition.
old = "  private final ExecutorService mExecutor = Executors.newSingleThreadExecutor();\n  private final Handler mMain = new Handler(Looper.getMainLooper());"
new = "  private final ExecutorService mExecutor = Executors.newSingleThreadExecutor();\n  private final ExecutorService mConvenienceExecutor = Executors.newSingleThreadExecutor();\n  private final Handler mMain = new Handler(Looper.getMainLooper());"
if "mConvenienceExecutor" not in s:
    if old not in s: raise SystemExit("convenience executor anchor not found")
    s = s.replace(old, new, 1)

old = "  private Points mLastPublishedPoints = new Points();"
new = """  private Points mLastPublishedPoints = new Points();
  private static final long CONVENIENCE_REFRESH_MS = 3 * 60 * 1000L;
  private static final long CONVENIENCE_RETRY_MS = 30 * 1000L;
  private static final float CONVENIENCE_REFRESH_DISTANCE_M = 800.0f;
  private long mLastConvenienceRequestTime;
  private double mLastConvenienceLat = Double.NaN;
  private double mLastConvenienceLon = Double.NaN;
  private boolean mConvenienceProbePosted;"""
if "CONVENIENCE_REFRESH_MS" not in s:
    if old not in s: raise SystemExit("convenience state anchor not found")
    s = s.replace(old, new, 1)

old = "    requestNearbySignalsIfNeeded(lat, lon, now);\n\n    if (now - mLastRequestTime < REFRESH_MS && !movedEnough(lat, lon))"
new = """    requestNearbySignalsIfNeeded(lat, lon, now);
    requestConvenienceIfNeeded(lat, lon, now);

    if (now - mLastRequestTime < REFRESH_MS && !movedEnough(lat, lon))"""
if "requestConvenienceIfNeeded(lat, lon, now);" not in s:
    if old not in s: raise SystemExit("onLocation convenience scheduler anchor not found")
    s = s.replace(old, new, 1)

anchor = "  private boolean movedEnough(double lat, double lon)\n  {"
helpers = r'''  private void requestConvenienceIfNeeded(double lat, double lon, long now)
  {
    if (!mConvenienceProbePosted)
    {
      mConvenienceProbePosted = true;
      postConvenienceProbe(lat, lon);
    }
    if (now - mLastConvenienceRequestTime < CONVENIENCE_REFRESH_MS && !movedEnoughConvenience(lat, lon))
      return;
    mLastConvenienceRequestTime = now;
    mLastConvenienceLat = lat;
    mLastConvenienceLon = lon;
    mConvenienceExecutor.execute(() -> refreshConvenience(lat, lon));
  }

  private boolean movedEnoughConvenience(double lat, double lon)
  {
    if (Double.isNaN(mLastConvenienceLat) || Double.isNaN(mLastConvenienceLon))
      return true;
    float[] result = new float[1];
    Location.distanceBetween(mLastConvenienceLat, mLastConvenienceLon, lat, lon, result);
    return result[0] >= CONVENIENCE_REFRESH_DISTANCE_M;
  }

  private void refreshConvenience(double lat, double lon)
  {
    String[] endpoints = {
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter"
    };
    String query = buildConvenienceQuery(lat, lon);
    String lastError = "";
    for (String endpoint : endpoints)
    {
      try
      {
        Points stores = parseOverpass(new JSONObject(post(endpoint, query)));
        if (stores.size() == 0)
          throw new IllegalStateException("Overpass returned zero convenience stores");
        postIndependentConvenience(stores);
        Log.i(TAG, "CB6-CONVENIENCE fetched=" + stores.size() + " classified=" + stores.size()
            + " endpoint=" + endpoint);
        return;
      }
      catch (Exception e)
      {
        lastError = e.getClass().getSimpleName() + ": " + String.valueOf(e.getMessage());
        Log.w(TAG, "CB6-CONVENIENCE endpoint failed: " + endpoint, e);
      }
    }
    mLastConvenienceRequestTime =
        System.currentTimeMillis() - CONVENIENCE_REFRESH_MS + CONVENIENCE_RETRY_MS;
    Log.w(TAG, "CB6-CONVENIENCE fetch failed; retained existing stores; retry scheduled: " + lastError);
  }

  private static boolean isConvenienceKind(int kind)
  {
    return (kind >= 1 && kind <= 6) || kind == 8 || kind == 9;
  }

  private void postIndependentConvenience(@NonNull Points stores)
  {
    mMain.post(() -> {
      Points merged = new Points();
      for (int i = 0; i < mLastPublishedPoints.size() && merged.size() < MAX_POINTS; ++i)
      {
        int kind = mLastPublishedPoints.kind.get(i);
        if (isConvenienceKind(kind))
          continue;
        merged.add(mLastPublishedPoints.lat.get(i), mLastPublishedPoints.lon.get(i), kind);
      }
      for (int i = 0; i < stores.size() && merged.size() < MAX_POINTS; ++i)
      {
        int kind = stores.kind.get(i);
        if (isConvenienceKind(kind))
          merged.add(stores.lat.get(i), stores.lon.get(i), kind);
      }
      mLastPublishedPoints = merged.copy();
      Framework.nativeSetCb6DrivingMarks(merged.lats(), merged.lons(), kindsForCurrentDirection(merged));
      Log.i(TAG, "CB6-CONVENIENCE JNI stores=" + stores.size() + " totalMarks=" + merged.size());
    });
  }

  private void postConvenienceProbe(double lat, double lon)
  {
    // Temporary real-device diagnostic: one generic convenience mark about 120 m east.
    // A successful network store refresh replaces this probe automatically.
    Points probe = new Points();
    double cos = Math.cos(Math.toRadians(lat));
    double deltaLon = 120.0 / (111320.0 * Math.max(0.2, cos));
    probe.add(lat, lon + deltaLon, 6);
    postIndependentConvenience(probe);
    Log.i(TAG, "CB6-CONVENIENCE PROBE posted about 120m east of current position");
  }

'''
if "private void refreshConvenience(double lat, double lon)" not in s:
    if anchor not in s: raise SystemExit("convenience helper anchor not found")
    s = s.replace(anchor, helpers + anchor, 1)

required = (
    "mConvenienceExecutor = Executors.newSingleThreadExecutor()",
    "requestConvenienceIfNeeded(lat, lon, now);",
    "private void refreshConvenience(double lat, double lon)",
    "String query = buildConvenienceQuery(lat, lon);",
    "private void postIndependentConvenience(@NonNull Points stores)",
    "CB6-CONVENIENCE fetched=",
    "CB6-CONVENIENCE JNI stores=",
    "CB6-CONVENIENCE PROBE posted about 120m east",
)
missing = [x for x in required if x not in s]
if missing: raise SystemExit("dedicated convenience path missing: " + ", ".join(missing))

# Frozen signal policy guard: this patch must not rewrite signal acquisition/render policy.
for token in (
    "NEAR_REFRESH_MS = 45 * 1000L",
    "NEAR_RETRY_MS = 12 * 1000L",
    "NEAR_REFRESH_DISTANCE_M = 250.0f",
    "NEAR_SIGNAL_RADIUS_M = 3000",
    "postNearbySignals(nearby, lat, lon);",
):
    if token not in s: raise SystemExit("frozen signal policy missing before convenience patch: " + token)

mgr.write_text(s, encoding="utf-8")
print("CB6 convenience acquisition isolated from signal flow; diagnostic probe/logging enabled")
