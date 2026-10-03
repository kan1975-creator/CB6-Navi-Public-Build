#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

# Preserve the proven Run #138 DebugMarkPoint renderer and only change signal
# visibility/size selection. 1 km is hidden by starting at z15. All signals use
# the normal/slim icon through the 200 m class of view; only nearby signals inside
# the vehicle's forward cone grow at closer zooms.
# Signal marks are kept non-displaceable/POI with depth testing disabled so that
# nearby physical traffic signals are not dropped by label/POI collision handling.
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text(encoding="utf-8")

pat = re.compile(
    r'class Cb6SignalMark final : public DebugMarkPoint\n    \{\n    public:\n'
    r'      explicit Cb6SignalMark\(m2::PointD const & pt\) : DebugMarkPoint\(pt\) \{\}\n'
    r'      drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames\(\) const override\n'
    r'      \{.*?\n      \}\n'
    r'      int GetMinZoom\(\) const override \{ return \d+; \}\n'
    r'(?:      bool SymbolIsPOI\(\) const override \{ return true; \}\n)?'
    r'(?:      bool IsNonDisplaceable\(\) const override \{ return true; \}\n)?'
    r'(?:      bool GetDepthTestEnabled\(\) const override \{ return false; \}\n)?'
    r'\n    private:\n'
    r'      bool m_forward = false;\n'
    r'    \};', re.S)
new_class = '''class Cb6SignalMark final : public DebugMarkPoint
    {
    public:
      explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt) {}
      void SetForward(bool forward) { m_forward = forward; }
      drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames() const override
      {
        auto symbols = make_unique_dp<SymbolNameZoomInfo>();
        // z15 ~= 500 m class: normal slim signal. z16 (about 200 m) stays normal.
        symbols->insert({15, "cb6-signal"});
        // Only a signal in the current travel direction is emphasized when close.
        if (m_forward)
        {
          symbols->insert({17, "cb6-signal-m"});
          symbols->insert({19, "cb6-signal-l"});
        }
        return symbols;
      }
      int GetMinZoom() const override { return 15; }
      bool SymbolIsPOI() const override { return true; }
      bool IsNonDisplaceable() const override { return true; }
      bool GetDepthTestEnabled() const override { return false; }

    private:
      bool m_forward = false;
    };'''
s, n = pat.subn(new_class, s, count=1)
if n != 1:
    # Also accept the v1.6 class before v1.8 has been applied.
    pat_v16 = re.compile(
        r'class Cb6SignalMark final : public DebugMarkPoint\n    \{\n    public:\n'
        r'      explicit Cb6SignalMark\(m2::PointD const & pt\) : DebugMarkPoint\(pt\) \{\}\n'
        r'      drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames\(\) const override\n'
        r'      \{.*?\n      \}\n'
        r'      int GetMinZoom\(\) const override \{ return \d+; \}\n'
        r'(?:      bool SymbolIsPOI\(\) const override \{ return true; \}\n)?'
        r'(?:      bool IsNonDisplaceable\(\) const override \{ return true; \}\n)?'
        r'(?:      bool GetDepthTestEnabled\(\) const override \{ return false; \}\n)?'
        r'    \};', re.S)
    s, n = pat_v16.subn(new_class, s, count=1)
if n != 1:
    if not all(token in s for token in (
        'void SetForward(bool forward)',
        'bool SymbolIsPOI() const override { return true; }',
        'bool IsNonDisplaceable() const override { return true; }',
        'bool GetDepthTestEnabled() const override { return false; }')):
        raise SystemExit("Cb6SignalMark forward/non-displaceable policy replacement point not found")

old_create = '''      if (static_cast<int>(kinds[i]) == 7)
      {
        session.CreateUserMark<Cb6SignalMark>(pt);
        continue;
      }'''
old_create_v18 = '''      if (static_cast<int>(kinds[i]) == 7 || static_cast<int>(kinds[i]) == 22)
      {
        session.CreateUserMark<Cb6SignalMark>(pt, static_cast<int>(kinds[i]) == 22);
        continue;
      }'''
new_create = '''      if (static_cast<int>(kinds[i]) == 7 || static_cast<int>(kinds[i]) == 22)
      {
        auto * mark = session.CreateUserMark<Cb6SignalMark>(pt);
        mark->SetForward(static_cast<int>(kinds[i]) == 22);
        continue;
      }'''
if old_create in s:
    s = s.replace(old_create, new_create, 1)
elif old_create_v18 in s:
    s = s.replace(old_create_v18, new_create, 1)
elif new_create not in s:
    raise SystemExit("Cb6SignalMark create branch replacement point not found")
fw.write_text(s, encoding="utf-8")

mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
m = mgr.read_text(encoding="utf-8")

# Current position/bearing used only to choose emphasis; cached data stays unchanged.
field_anchor = '  private boolean mCacheApplied;\n'
fields = '''  private boolean mCacheApplied;
  private double mCurrentLat = Double.NaN;
  private double mCurrentLon = Double.NaN;
  private float mCurrentBearing;
  private boolean mHasCurrentBearing;
  private static final int KIND_SIGNAL_FORWARD = 22;
  private static final float FORWARD_SIGNAL_MAX_M = 450.0f;
  private static final float FORWARD_CONE_DEG = 45.0f;
'''
if 'KIND_SIGNAL_FORWARD = 22' not in m:
    if field_anchor not in m:
        raise SystemExit("manager field anchor not found")
    m = m.replace(field_anchor, fields, 1)

loc_anchor = '  public void onLocation(@NonNull Location location)\n  {\n'
loc_new = '''  public void onLocation(@NonNull Location location)
  {
    mCurrentLat = location.getLatitude();
    mCurrentLon = location.getLongitude();
    if (location.hasBearing())
    {
      mCurrentBearing = location.getBearing();
      mHasCurrentBearing = true;
    }
'''
if 'mCurrentLat = location.getLatitude();' not in m:
    if loc_anchor not in m:
        raise SystemExit("manager onLocation anchor not found")
    m = m.replace(loc_anchor, loc_new, 1)

post_old = 'Framework.nativeSetCb6DrivingMarks(points.lats(), points.lons(), points.kinds());'
post_new = 'Framework.nativeSetCb6DrivingMarks(points.lats(), points.lons(), kindsForCurrentDirection(points));'
if post_old in m:
    m = m.replace(post_old, post_new)
elif post_new not in m:
    raise SystemExit("manager JNI post replacement point not found")

# In dense urban areas the 5 km signal query can exceed MAX_SIGNAL_POINTS.
# Overpass result order is not distance order, so a simple first-N cap can discard
# signals immediately around the vehicle. Parse signal-only responses by distance
# and retain the nearest signals first. Query radius/cache/JNI coordinates stay unchanged.
signal_call_old = 'Points candidate = parseOverpass(new JSONObject(post(endpoint, signalQuery)));'
signal_call_new = 'Points candidate = parseSignalsNearFirst(new JSONObject(post(endpoint, signalQuery)), lat, lon);'
if signal_call_old in m:
    m = m.replace(signal_call_old, signal_call_new, 1)
elif signal_call_new not in m:
    raise SystemExit("signal parse call replacement point not found")

parse_anchor = '  private static Points parseOverpass(JSONObject root) throws Exception\n'
near_parser = '''  private static Points parseSignalsNearFirst(JSONObject root, double originLat, double originLon) throws Exception
  {
    Points out = new Points();
    JSONArray elements = root.optJSONArray("elements");
    if (elements == null)
      return out;

    ArrayList<double[]> signals = new ArrayList<>();
    float[] distance = new float[1];
    for (int i = 0; i < elements.length(); ++i)
    {
      JSONObject e = elements.optJSONObject(i);
      if (e == null)
        continue;
      JSONObject tags = e.optJSONObject("tags");
      if (tags == null || !"traffic_signals".equals(tags.optString("highway", "")))
        continue;
      double[] pos = positionOf(e);
      if (pos == null)
        continue;
      Location.distanceBetween(originLat, originLon, pos[0], pos[1], distance);
      signals.add(new double[] {pos[0], pos[1], distance[0]});
    }

    signals.sort((a, b) -> Double.compare(a[2], b[2]));
    int limit = Math.min(signals.size(), MAX_SIGNAL_POINTS);
    for (int i = 0; i < limit; ++i)
    {
      double[] pos = signals.get(i);
      out.add(pos[0], pos[1], KIND_SIGNAL_FULL);
    }
    return out;
  }

'''
if 'private static Points parseSignalsNearFirst' not in m:
    if parse_anchor not in m:
        raise SystemExit("parseOverpass anchor not found")
    m = m.replace(parse_anchor, near_parser + parse_anchor, 1)

helper_anchor = '  private void showStatus(@NonNull String text)\n'
helper = '''  private int[] kindsForCurrentDirection(@NonNull Points points)
  {
    int[] out = points.kinds();
    if (!mHasCurrentBearing || Double.isNaN(mCurrentLat) || Double.isNaN(mCurrentLon))
      return out;

    float[] result = new float[3];
    for (int i = 0; i < out.length; ++i)
    {
      if (out[i] != KIND_SIGNAL_FULL)
        continue;
      Location.distanceBetween(mCurrentLat, mCurrentLon, points.lat.get(i), points.lon.get(i), result);
      if (result[0] > FORWARD_SIGNAL_MAX_M)
        continue;
      float delta = Math.abs(((result[1] - mCurrentBearing + 540.0f) % 360.0f) - 180.0f);
      if (delta <= FORWARD_CONE_DEG)
        out[i] = KIND_SIGNAL_FORWARD;
    }
    return out;
  }

'''
if 'private int[] kindsForCurrentDirection' not in m:
    if helper_anchor not in m:
        raise SystemExit("manager helper anchor not found")
    m = m.replace(helper_anchor, helper + helper_anchor, 1)

mgr.write_text(m, encoding="utf-8")
print("CB6 v1.8 applied: hide at 1km, normal through 200m, enlarge only forward nearby signals; nearest signals retained before cap; physical signals non-displaceable")
