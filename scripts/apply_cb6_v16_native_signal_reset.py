#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

# CB6 v1.6 real-signal render/fetch fix.
# Run #133 proved DebugMarkPoint-derived cb6-signal-l renders correctly.
# Run #136 then showed no real signals after removing the synthetic probe, which
# strongly points at the input path. The old Overpass request mixed a 5 km signal
# query with a much heavier 6.5 km convenience-store query and stop query; on a
# mobile connection that whole request can time out before any signal reaches JNI.
# This patch keeps the proven renderer but fetches traffic signals first with a
# lightweight dedicated request, then optionally enriches with convenience/stop.
# Native MapCSS traffic-signal rendering remains disabled.

def strip_signal_rules(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out = []
    block = []
    in_block = False
    for line in lines:
        if not in_block:
            block = [line]
            if "{" in line:
                in_block = True
                if "}" in line:
                    joined = "".join(block)
                    if "[highway=traffic_signals]" not in joined:
                        out.extend(block)
                    block = []
                    in_block = False
            elif line.strip().startswith("/*") or line.strip().startswith("//") or not line.strip():
                out.append(line)
            else:
                in_block = True
        else:
            block.append(line)
            if "}" in line:
                joined = "".join(block)
                if "[highway=traffic_signals]" not in joined:
                    out.extend(block)
                block = []
                in_block = False
    if block:
        out.extend(block)
    result = "".join(out)
    result = re.sub(r'\n?/\* CB6 v1\.6:[^*]*traffic-signal[^*]*\*/\n?', "\n", result, flags=re.I)
    result = re.sub(r'\n?/\* CB6 native MWM traffic signal fallback\. \*/\n?', "\n", result)
    return result

for p in sorted((ROOT / "data/styles").glob("*/include/Icons.mapcss")):
    before = p.read_text(encoding="utf-8")
    after = strip_signal_rules(before)
    if after != before:
        p.write_text(after, encoding="utf-8")
        print("native signal rule removed:", p.relative_to(ROOT))

u = ROOT / "libs/map/user_mark.cpp"
us = u.read_text(encoding="utf-8")
us, n = re.subn(
    r'Cb6DrivingMark::Cb6DrivingMark\(m2::PointD const & ptOrg\)\n  : UserMark\(ptOrg, UserMark::Type::CB6_DRIVING\)\n\{\}',
    'Cb6DrivingMark::Cb6DrivingMark(m2::PointD const & ptOrg)\n  : UserMark(ptOrg, UserMark::Type::DEBUG_MARK)\n{}',
    us, count=1)
if n != 1:
    raise SystemExit("Cb6DrivingMark DEBUG_MARK routing replacement failed")

signal_case = re.compile(
    r'  case 7:\n(?:    symbols->insert\([^\n]+\);\n)+    break;'
    r'(?:\n  case 20:\n(?:    symbols->insert\([^\n]+\);\n)+    break;)?'
    r'(?:\n  case 21:\n(?:    symbols->insert\([^\n]+\);\n)+    break;)?'
)
replacement = '''  case 7:\n    symbols->insert({1, "cb6-signal-l"});\n    break;'''
us, n = signal_case.subn(replacement, us, count=1)
if n != 1:
    raise SystemExit("signal UserMark case replacement failed")

us, n = re.subn(
    r'int Cb6DrivingMark::GetMinZoom\(\) const\n\{.*?\n\}',
    '''int Cb6DrivingMark::GetMinZoom() const\n{\n  if (m_kind == 7)\n    return 1;\n  if (m_kind == 20)\n    return 21;\n  if (m_kind == 0)\n    return 13;\n  return 11;\n}''',
    us, count=1, flags=re.S)
if n != 1:
    raise SystemExit("GetMinZoom replacement failed")
u.write_text(us, encoding="utf-8")
print("CB6 supplemental mark group routed through DEBUG_MARK")

fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
fws = fw.read_text(encoding="utf-8")
old_group = '''    session.ClearGroup(UserMark::Type::CB6_DRIVING);'''
new_group = '''    session.ClearGroup(UserMark::Type::DEBUG_MARK);\n    session.SetIsVisible(UserMark::Type::DEBUG_MARK, true);'''
if old_group in fws:
    fws = fws.replace(old_group, new_group, 1)
elif new_group not in fws:
    raise SystemExit("CB6 JNI visibility/group replacement point not found")

loop = '''    for (jsize i = 0; i < n; ++i)\n    {\n      if (lats[i] < -90.0 || lats[i] > 90.0 || lons[i] < -180.0 || lons[i] > 180.0)\n        continue;\n      auto * mark = session.CreateUserMark<Cb6DrivingMark>(mercator::FromLatLon(lats[i], lons[i]));\n      mark->SetKind(static_cast<int>(kinds[i]));\n    }'''
replacement_loop = '''    class Cb6SignalMark final : public DebugMarkPoint\n    {\n    public:\n      explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt) {}\n      drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames() const override\n      {\n        auto symbols = make_unique_dp<SymbolNameZoomInfo>();\n        symbols->insert({1, "cb6-signal-l"});\n        return symbols;\n      }\n      int GetMinZoom() const override { return 1; }\n      bool SymbolIsPOI() const override { return true; }\n      bool IsNonDisplaceable() const override { return true; }\n      bool GetDepthTestEnabled() const override { return false; }\n    };\n\n    for (jsize i = 0; i < n; ++i)\n    {\n      if (lats[i] < -90.0 || lats[i] > 90.0 || lons[i] < -180.0 || lons[i] > 180.0)\n        continue;\n      auto const pt = mercator::FromLatLon(lats[i], lons[i]);\n      if (static_cast<int>(kinds[i]) == 7)\n      {\n        session.CreateUserMark<Cb6SignalMark>(pt);\n        continue;\n      }\n      auto * mark = session.CreateUserMark<Cb6DrivingMark>(pt);\n      mark->SetKind(static_cast<int>(kinds[i]));\n    }\n    session.NotifyChanges();'''
if loop not in fws:
    raise SystemExit("CB6 JNI mark loop replacement point not found")
fws = fws.replace(loop, replacement_loop, 1)

required = (
    'class Cb6SignalMark final : public DebugMarkPoint',
    'symbols->insert({1, "cb6-signal-l"});',
    'if (static_cast<int>(kinds[i]) == 7)',
    'session.CreateUserMark<Cb6SignalMark>(pt);',
    'session.NotifyChanges();',
)
missing = [x for x in required if x not in fws]
if missing:
    raise SystemExit("CB6 real-signal path missing: " + ", ".join(missing))
for forbidden in ('Cb6SignalDebugProbe', 'stockCb6->SetKind(21)', 'testLat = lats[n - 1]'):
    if forbidden in fws:
        raise SystemExit("diagnostic probe still present: " + forbidden)
fw.write_text(fws, encoding="utf-8")
print("real traffic signals use proven DebugMark-derived cb6-signal-l renderer")

# Remove the synthetic forced TEST point from the Java manager now that the
# renderer path has been proven on-device. Real Overpass/cache signals stay.
mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
ms = mgr.read_text(encoding="utf-8")
ms = ms.replace('  private double mDiagnosticLat = Double.NaN;\n  private double mDiagnosticLon = Double.NaN;\n', '')
ms = re.sub(
    r'\n    // Keep one synthetic signal about 120 m north of the current position\..*?\n    if \(Double\.isNaN\(mDiagnosticLat\) \|\| Double\.isNaN\(mDiagnosticLon\)\)\n    \{.*?\n    \}\n',
    '\n', ms, count=1, flags=re.S)
ms = ms.replace('    if (!hasUsableCache())\n      postDiagnosticOnly();\n', '')
ms = ms.replace('      postDiagnosticOnly();\n', '')
ms = re.sub(r'\n  private void postDiagnosticOnly\(\)\n  \{.*?\n  \}\n\n  private void postPoints',
            '\n  private void postPoints', ms, count=1, flags=re.S)
old_post = '''    mMain.post(() -> {\n      Points merged = points.copy();\n      if (!Double.isNaN(mDiagnosticLat) && !Double.isNaN(mDiagnosticLon))\n        merged.add(mDiagnosticLat, mDiagnosticLon, KIND_SIGNAL_FULL);\n      Framework.nativeSetCb6DrivingMarks(merged.lats(), merged.lons(), merged.kinds());\n      String msg = "SIG " + source + ": 実信号" + points.signalCount() + "件 + TEST1件 / 全"\n          + merged.size() + "件 → JNI";\n      showStatus(msg);\n      Log.i(TAG, msg);\n    });'''
new_post = '''    mMain.post(() -> {\n      Framework.nativeSetCb6DrivingMarks(points.lats(), points.lons(), points.kinds());\n      String msg = "SIG " + source + ": 実信号" + points.signalCount() + "件 / 全"\n          + points.size() + "件 → JNI";\n      showStatus(msg);\n      Log.i(TAG, msg);\n    });'''
if old_post not in ms:
    raise SystemExit("CB6 manager diagnostic merge block not found")
ms = ms.replace(old_post, new_post, 1)
for forbidden in ('mDiagnosticLat', 'mDiagnosticLon', 'postDiagnosticOnly()', 'TEST1件', 'SIG TEST'):
    if forbidden in ms:
        raise SystemExit("forced diagnostic remains in manager: " + forbidden)

# Split the heavy combined Overpass request. Signals are fetched first and posted
# even if the optional convenience/stop enrichment fails. This prevents a large
# POI response from suppressing all traffic signals on slow mobile links.
refresh_pattern = re.compile(
    r'  private void refresh\(double lat, double lon\)\n  \{.*?\n  \}\n\n  private void postPoints',
    re.S)
new_refresh = '''  private void refresh(double lat, double lon)\n  {\n    String[] endpoints = {\n        "https://overpass-api.de/api/interpreter",\n        "https://overpass.kumi.systems/api/interpreter",\n        "https://overpass.nchc.org.tw/api/interpreter"\n    };\n\n    Points signals = null;\n    String lastError = "";\n    String signalQuery = buildSignalQuery(lat, lon);\n    for (String endpoint : endpoints)\n    {\n      try\n      {\n        Points candidate = parseOverpass(new JSONObject(post(endpoint, signalQuery)));\n        if (candidate.signalCount() == 0)\n          throw new IllegalStateException("Overpass returned zero traffic signals");\n        signals = candidate;\n        break;\n      }\n      catch (Exception e)\n      {\n        lastError = e.getClass().getSimpleName() + ": " + String.valueOf(e.getMessage());\n        Log.w(TAG, "signal endpoint failed: " + endpoint, e);\n      }\n    }\n\n    if (signals == null)\n    {\n      showStatus("SIG NET: 信号取得失敗 " + lastError);\n      mLastRequestTime = System.currentTimeMillis() - REFRESH_MS + 60_000L;\n      applySavedCache();\n      return;\n    }\n\n    Points merged = signals.copy();\n    String poiQuery = buildPoiQuery(lat, lon);\n    for (String endpoint : endpoints)\n    {\n      try\n      {\n        Points extras = parseOverpass(new JSONObject(post(endpoint, poiQuery)));\n        merged.addAllNonSignals(extras);\n        break;\n      }\n      catch (Exception e)\n      {\n        Log.w(TAG, "optional POI endpoint failed: " + endpoint, e);\n      }\n    }\n\n    try\n    {\n      mContext.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit()\n              .putString(CACHE, merged.toJson().toString())\n              .putLong(CACHE_TIME, System.currentTimeMillis())\n              .apply();\n    }\n    catch (Exception e)\n    {\n      Log.w(TAG, "cache write failed", e);\n    }\n    postPoints(merged, "NET");\n    Log.i(TAG, "loaded " + merged.size() + " supplemental points, signals=" + merged.signalCount());\n  }\n\n  private void postPoints'''
ms, n = refresh_pattern.subn(new_refresh, ms, count=1)
if n != 1:
    raise SystemExit("CB6 manager refresh replacement failed")

build_pattern = re.compile(
    r'  private static String buildQuery\(double lat, double lon\)\n  \{.*?\n  \}\n\n  private static String post',
    re.S)
new_build = '''  private static String buildSignalQuery(double lat, double lon)\n  {\n    String ll = String.format(Locale.US, "%.6f,%.6f", lat, lon);\n    return "[out:json][timeout:18];("\n        + "node(around:5000," + ll + ")[highway=traffic_signals];"\n        + ");out body;";\n  }\n\n  private static String buildPoiQuery(double lat, double lon)\n  {\n    String ll = String.format(Locale.US, "%.6f,%.6f", lat, lon);\n    return "[out:json][timeout:18];("\n        + "nwr(around:3500," + ll + ")[shop=convenience];"\n        + "node(around:2500," + ll + ")[highway=stop];"\n        + ");out center tags;";\n  }\n\n  private static String post'''
ms, n = build_pattern.subn(new_build, ms, count=1)
if n != 1:
    raise SystemExit("CB6 manager query split replacement failed")

copy_anchor = '''    Points copy()\n    {\n      Points out = new Points();\n      out.lat.addAll(lat);\n      out.lon.addAll(lon);\n      out.kind.addAll(kind);\n      return out;\n    }\n\n    int size()'''
copy_replacement = '''    Points copy()\n    {\n      Points out = new Points();\n      out.lat.addAll(lat);\n      out.lon.addAll(lon);\n      out.kind.addAll(kind);\n      return out;\n    }\n\n    void addAllNonSignals(Points other)\n    {\n      for (int i = 0; i < other.kind.size() && size() < MAX_POINTS; ++i)\n      {\n        int k = other.kind.get(i);\n        if (k == KIND_SIGNAL_FULL || k == KIND_SIGNAL_CLUSTER)\n          continue;\n        add(other.lat.get(i), other.lon.get(i), k);\n      }\n    }\n\n    int size()'''
if copy_anchor not in ms:
    raise SystemExit("CB6 manager Points.copy anchor not found")
ms = ms.replace(copy_anchor, copy_replacement, 1)

for required_java in (
    'String signalQuery = buildSignalQuery(lat, lon);',
    'postPoints(merged, "NET");',
    'private static String buildSignalQuery',
    'node(around:5000,',
    'private static String buildPoiQuery',
    'void addAllNonSignals(Points other)',
):
    if required_java not in ms:
        raise SystemExit("split Overpass path missing: " + required_java)

mgr.write_text(ms, encoding="utf-8")
print("forced synthetic signal removed; signal-only Overpass fetch now precedes optional POI enrichment")

print("CB6 v1.6 real-signal fix applied; dedicated lightweight signal fetch enabled.")
