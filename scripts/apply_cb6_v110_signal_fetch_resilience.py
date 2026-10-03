#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
s = mgr.read_text(encoding="utf-8")

# v1.10 hardens traffic-signal acquisition while preserving already-published POIs.
# This is important because nativeSetCb6DrivingMarks replaces the whole CB6_DRIVING
# group. A signal-only publish must therefore merge with retained non-signal marks.

old = '''  private static final float REFRESH_DISTANCE_M = 2200.0f;\n  private static final int MAX_POINTS = 2200;'''
new = '''  private static final float REFRESH_DISTANCE_M = 2200.0f;\n  private static final long NEAR_REFRESH_MS = 90 * 1000L;\n  private static final long NEAR_RETRY_MS = 20 * 1000L;\n  private static final float NEAR_REFRESH_DISTANCE_M = 500.0f;\n  private static final int NEAR_SIGNAL_RADIUS_M = 2000;\n  private static final int MAX_POINTS = 2200;'''
if 'NEAR_SIGNAL_RADIUS_M = 2000' not in s:
    if old not in s: raise SystemExit("v1.10 constants anchor not found")
    s = s.replace(old, new, 1)

old = '''  private long mLastRequestTime;\n  private double mLastLat = Double.NaN;\n  private double mLastLon = Double.NaN;'''
new = '''  private long mLastRequestTime;\n  private double mLastLat = Double.NaN;\n  private double mLastLon = Double.NaN;\n  private long mLastNearRequestTime;\n  private double mLastNearLat = Double.NaN;\n  private double mLastNearLon = Double.NaN;\n  private Points mLastPublishedPoints = new Points();'''
if 'mLastNearRequestTime' not in s:
    if old not in s: raise SystemExit("v1.10 field anchor not found")
    s = s.replace(old, new, 1)

old = '''    final long now = System.currentTimeMillis();\n    final double lat = location.getLatitude();\n    final double lon = location.getLongitude();\n    if (now - mLastRequestTime < REFRESH_MS && !movedEnough(lat, lon))\n      return;'''
new = '''    final long now = System.currentTimeMillis();\n    final double lat = location.getLatitude();\n    final double lon = location.getLongitude();\n\n    requestNearbySignalsIfNeeded(lat, lon, now);\n\n    if (now - mLastRequestTime < REFRESH_MS && !movedEnough(lat, lon))\n      return;'''
if 'requestNearbySignalsIfNeeded(lat, lon, now);' not in s:
    if old not in s: raise SystemExit("v1.10 onLocation anchor not found")
    s = s.replace(old, new, 1)

anchor = '''  private boolean movedEnough(double lat, double lon)\n  {'''
helpers = '''  private void requestNearbySignalsIfNeeded(double lat, double lon, long now)\n  {\n    if (now - mLastNearRequestTime < NEAR_REFRESH_MS && !movedEnoughNear(lat, lon))\n      return;\n    mLastNearRequestTime = now;\n    mLastNearLat = lat;\n    mLastNearLon = lon;\n    mExecutor.execute(() -> refreshNearbySignals(lat, lon));\n  }\n\n  private boolean movedEnoughNear(double lat, double lon)\n  {\n    if (Double.isNaN(mLastNearLat) || Double.isNaN(mLastNearLon))\n      return true;\n    float[] result = new float[1];\n    Location.distanceBetween(mLastNearLat, mLastNearLon, lat, lon, result);\n    return result[0] >= NEAR_REFRESH_DISTANCE_M;\n  }\n\n  private void refreshNearbySignals(double lat, double lon)\n  {\n    String[] endpoints = {\n        "https://overpass-api.de/api/interpreter",\n        "https://overpass.kumi.systems/api/interpreter",\n        "https://overpass.nchc.org.tw/api/interpreter"\n    };\n    String query = buildNearSignalQuery(lat, lon);\n    String lastError = "";\n    for (String endpoint : endpoints)\n    {\n      try\n      {\n        Points nearby = parseSignalsNearFirst(new JSONObject(postQuick(endpoint, query)), lat, lon);\n        if (nearby.signalCount() == 0)\n        {\n          Log.i(TAG, "near signal refresh returned zero signals; preserving current marks");\n          return;\n        }\n        postNearbySignals(nearby, lat, lon);\n        Log.i(TAG, "near signal refresh loaded " + nearby.signalCount() + " signals");\n        return;\n      }\n      catch (Exception e)\n      {\n        lastError = e.getClass().getSimpleName() + ": " + String.valueOf(e.getMessage());\n        Log.w(TAG, "near signal endpoint failed: " + endpoint, e);\n      }\n    }\n    mLastNearRequestTime = System.currentTimeMillis() - NEAR_REFRESH_MS + NEAR_RETRY_MS;\n    Log.w(TAG, "near signal refresh failed; current marks preserved, retry scheduled: " + lastError);\n  }\n\n'''
if 'private void refreshNearbySignals(double lat, double lon)' not in s:
    if anchor not in s: raise SystemExit("v1.10 helper anchor not found")
    s = s.replace(anchor, helpers + anchor, 1)

# v1.9 publishes broad signals before POI enrichment. Since JNI replaces the whole
# group, convert that call to a preserving publisher which keeps convenience/stop marks.
s = s.replace('postPoints(signals, "NET-SIG");', 'postImmediateSignals(signals);', 1)

anchor = '''  private void postPoints(@NonNull Points points, @NonNull String source)\n  {'''
publishers = '''  private void postImmediateSignals(@NonNull Points signals)\n  {\n    mMain.post(() -> {\n      Points merged = new Points();\n      for (int i = 0; i < mLastPublishedPoints.size() && merged.size() < MAX_POINTS; ++i)\n      {\n        int k = mLastPublishedPoints.kind.get(i);\n        if (k == KIND_SIGNAL_FULL || k == KIND_SIGNAL_FORWARD || k == KIND_SIGNAL_CLUSTER)\n          continue;\n        merged.add(mLastPublishedPoints.lat.get(i), mLastPublishedPoints.lon.get(i), k);\n      }\n      for (int i = 0; i < signals.size() && merged.size() < MAX_POINTS; ++i)\n        merged.add(signals.lat.get(i), signals.lon.get(i), signals.kind.get(i));\n      mLastPublishedPoints = merged.copy();\n      Framework.nativeSetCb6DrivingMarks(merged.lats(), merged.lons(), kindsForCurrentDirection(merged));\n      Log.i(TAG, "SIG NET-SIG: immediate signals merged without clearing retained POIs; total=" + merged.size());\n    });\n  }\n\n  private void postNearbySignals(@NonNull Points nearby, double originLat, double originLon)\n  {\n    mMain.post(() -> {\n      Points merged = new Points();\n      float[] distance = new float[1];\n      for (int i = 0; i < mLastPublishedPoints.size() && merged.size() < MAX_POINTS; ++i)\n      {\n        int kind = mLastPublishedPoints.kind.get(i);\n        boolean signal = kind == KIND_SIGNAL_FULL || kind == KIND_SIGNAL_FORWARD || kind == KIND_SIGNAL_CLUSTER;\n        if (signal)\n        {\n          Location.distanceBetween(originLat, originLon, mLastPublishedPoints.lat.get(i), mLastPublishedPoints.lon.get(i), distance);\n          if (distance[0] <= NEAR_SIGNAL_RADIUS_M)\n            continue;\n        }\n        merged.add(mLastPublishedPoints.lat.get(i), mLastPublishedPoints.lon.get(i), kind);\n      }\n      for (int i = 0; i < nearby.size() && merged.size() < MAX_POINTS; ++i)\n        merged.add(nearby.lat.get(i), nearby.lon.get(i), KIND_SIGNAL_FULL);\n      mLastPublishedPoints = merged.copy();\n      Framework.nativeSetCb6DrivingMarks(merged.lats(), merged.lons(), kindsForCurrentDirection(merged));\n      Log.i(TAG, "SIG NEAR: " + nearby.signalCount() + " fresh nearby signals merged; total=" + merged.size());\n    });\n  }\n\n'''
if 'private void postImmediateSignals(@NonNull Points signals)' not in s:
    if anchor not in s: raise SystemExit("v1.10 publisher anchor not found")
    s = s.replace(anchor, publishers + anchor, 1)

old = '''    mMain.post(() -> {\n      Framework.nativeSetCb6DrivingMarks(points.lats(), points.lons(), kindsForCurrentDirection(points));'''
new = '''    mMain.post(() -> {\n      mLastPublishedPoints = points.copy();\n      Framework.nativeSetCb6DrivingMarks(points.lats(), points.lons(), kindsForCurrentDirection(points));'''
if 'mLastPublishedPoints = points.copy();' not in s:
    if old not in s: raise SystemExit("v1.10 postPoints state anchor not found")
    s = s.replace(old, new, 1)

anchor = '''  private static String buildSignalQuery(double lat, double lon)\n  {'''
near_query = '''  private static String buildNearSignalQuery(double lat, double lon)\n  {\n    String ll = String.format(Locale.US, "%.6f,%.6f", lat, lon);\n    return "[out:json][timeout:8];("\n        + "node(around:" + NEAR_SIGNAL_RADIUS_M + "," + ll + ")[highway=traffic_signals];"\n        + ");out body;";\n  }\n\n'''
if 'private static String buildNearSignalQuery' not in s:
    if anchor not in s: raise SystemExit("v1.10 near query anchor not found")
    s = s.replace(anchor, near_query + anchor, 1)

anchor = '''  private static String post(String endpoint, String query) throws Exception\n  {'''
quick_post = '''  private static String postQuick(String endpoint, String query) throws Exception\n  {\n    HttpURLConnection c = (HttpURLConnection) new URL(endpoint).openConnection();\n    c.setConnectTimeout(4000);\n    c.setReadTimeout(8000);\n    c.setRequestMethod("POST");\n    c.setDoOutput(true);\n    c.setRequestProperty("User-Agent", "CB6-Navi/NearSignal CoMaps-supplement");\n    c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");\n    byte[] body = ("data=" + URLEncoder.encode(query, StandardCharsets.UTF_8.name())).getBytes(StandardCharsets.UTF_8);\n    c.getOutputStream().write(body);\n    int code = c.getResponseCode();\n    InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();\n    if (in == null) throw new IllegalStateException("HTTP " + code);\n    try (BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8)))\n    {\n      StringBuilder out = new StringBuilder(); String line;\n      while ((line = br.readLine()) != null) out.append(line);\n      if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);\n      return out.toString();\n    }\n    finally { c.disconnect(); }\n  }\n\n'''
if 'private static String postQuick' not in s:
    if anchor not in s: raise SystemExit("v1.10 quick post anchor not found")
    s = s.replace(anchor, quick_post + anchor, 1)

required = (
    'postImmediateSignals(signals);', 'private void postImmediateSignals(@NonNull Points signals)',
    'KIND_SIGNAL_FORWARD = 22', 'FORWARD_SIGNAL_MAX_M = 450.0f', 'FORWARD_CONE_DEG = 45.0f',
    'parseSignalsNearFirst', 'MAX_SIGNAL_POINTS = 1400', 'requestNearbySignalsIfNeeded(lat, lon, now);',
    'postNearbySignals(nearby, lat, lon);',
    'mLastNearRequestTime = System.currentTimeMillis() - NEAR_REFRESH_MS + NEAR_RETRY_MS;',
)
missing = [x for x in required if x not in s]
if missing: raise SystemExit("v1.10 required behavior missing: " + ", ".join(missing))
if 'postPoints(signals, "NET-SIG");' in s:
    raise SystemExit("unsafe signal-only whole-group publisher still present")

mgr.write_text(s, encoding="utf-8")
print("CB6 v1.10 applied: nearby/broad signal refresh preserves convenience and stop marks")
