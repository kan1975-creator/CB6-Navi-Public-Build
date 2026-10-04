#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
REPO = Path(__file__).resolve().parents[2]
sdk = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk"
for src in ("convenience_brand_classifier.hpp","convenience_brand_classifier.cpp",
            "convenience_mwm_collector.hpp","convenience_mwm_collector.cpp"):
    shutil.copy2(REPO / "v2/poi/native" / src, sdk / src)
cmake = ROOT / "android/sdk/src/main/cpp/CMakeLists.txt"
cm = cmake.read_text()
anchor = "  app/organicmaps/sdk/Framework.cpp\n"
addition = ("  app/organicmaps/sdk/convenience_brand_classifier.cpp\n"
            "  app/organicmaps/sdk/convenience_mwm_collector.cpp\n")
if addition not in cm:
    if anchor not in cm: raise SystemExit("CMake anchor missing")
    cm = cm.replace(anchor, anchor + addition, 1)
cmake.write_text(cm)

# Dedicated ownership: never reuse traffic-light / CB6 driving mark groups.
uh = ROOT / "libs/map/user_mark.hpp"
s = uh.read_text()
old = "    TRAFFIC_LIGHT,\n    USER_MARK_TYPES_COUNT,"
signal_old = "    TRAFFIC_LIGHT,\n    CB6_SIGNAL,\n    USER_MARK_TYPES_COUNT,"
new = "    TRAFFIC_LIGHT,\n    CONVENIENCE,\n    USER_MARK_TYPES_COUNT,"
signal_new = "    TRAFFIC_LIGHT,\n    CONVENIENCE,\n    CB6_SIGNAL,\n    USER_MARK_TYPES_COUNT,"
if "    CONVENIENCE," not in s:
    if signal_old in s:
        s = s.replace(signal_old, signal_new, 1)
    elif old in s:
        s = s.replace(old, new, 1)
    else:
        raise SystemExit("UserMark type anchor missing")
uh.write_text(s)

# Keep DebugPrint exhaustive after adding the dedicated mark type.
ucpp = ROOT / "libs/map/user_mark.cpp"
us = ucpp.read_text()
case_anchor = '  case UserMark::Type::TRAFFIC_LIGHT: return "TRAFFIC_LIGHT";\n'
case_line = '  case UserMark::Type::CONVENIENCE: return "CONVENIENCE";\n'
if case_line not in us:
    if case_anchor not in us: raise SystemExit("UserMark DebugPrint anchor missing")
    us = us.replace(case_anchor, case_anchor + case_line, 1)
ucpp.write_text(us)

fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text()
inc = '#include "app/organicmaps/sdk/convenience_mwm_collector.hpp"\n'
if inc not in s:
    s = s.replace('#include "app/organicmaps/sdk/Framework.hpp"\n',
                  '#include "app/organicmaps/sdk/Framework.hpp"\n' + inc, 1)
anchor = "JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeClearApiPoints"
code = r'''
class Cb6ConvenienceMark final : public UserMark
{
public:
  explicit Cb6ConvenienceMark(m2::PointD const & pt) : UserMark(pt, UserMark::Type::CONVENIENCE) {}
  void SetKind(int kind) { m_kind = kind; }

  drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames() const override
  {
    auto symbols = make_unique_dp<SymbolNameZoomInfo>();
    char const * symbol = "cb6-convenience";
    switch (m_kind)
    {
    case 1: symbol = "cb6-seven"; break;
    case 2: symbol = "cb6-familymart"; break;
    case 3: symbol = "cb6-lawson"; break;
    case 4: symbol = "cb6-seicomart"; break;
    case 5: symbol = "cb6-mybasket"; break;
    case 8: symbol = "cb6-ministop"; break;
    case 9: symbol = "cb6-daily"; break;
    default: break;
    }
    LOG(LINFO, ("CB6-CONVENIENCE-DIAG symbol-selected", "kind", m_kind, "symbol", symbol));
    symbols->insert({12, symbol});
    return symbols;
  }
  int GetMinZoom() const override { return 12; }
  bool SymbolIsPOI() const override { return false; }
  bool IsNonDisplaceable() const override { return true; }
  bool IsMarkAboveText() const override { return true; }
  bool GetDepthTestEnabled() const override { return false; }

private:
  int m_kind;
};

static int Cb6ConvenienceKind(cb6::poi::ConvenienceBrand brand)
{
  using B = cb6::poi::ConvenienceBrand;
  switch (brand)
  {
  case B::SevenEleven: return 1;
  case B::FamilyMart: return 2;
  case B::Lawson: return 3;
  case B::Seicomart: return 4;
  case B::MyBasket: return 5;
  case B::Ministop: return 8;
  case B::DailyYamazaki: return 9;
  case B::Generic: return 6;
  }
  return 6;
}

JNIEXPORT jobjectArray JNICALL Java_app_organicmaps_sdk_Framework_nativeCb6CollectConvenienceMarks(
    JNIEnv * env, jclass, jdouble lat, jdouble lon, jint radiusMeters, jint scale)
{
  jclass const doubleArrayClass = env->FindClass("[D");
  jobjectArray out = env->NewObjectArray(3, doubleArrayClass, nullptr);
  if (!g_framework || radiusMeters <= 0)
    return out;
  auto const center = mercator::FromLatLon(lat, lon);
  auto const delta = mercator::MetersToMercator(radiusMeters);
  m2::RectD const rect(center.x-delta, center.y-delta, center.x+delta, center.y+delta);
  auto const pois = cb6::poi::CollectConveniencePois(frm()->GetDataSource(), rect, scale);
  auto const n = static_cast<jsize>(std::min<size_t>(pois.size(), 250));
  std::array<size_t, 10> brandCounts{};
  for (jsize i = 0; i < n; ++i) { auto const k = Cb6ConvenienceKind(pois[static_cast<size_t>(i)].m_identity.m_brand); if (k >= 0 && static_cast<size_t>(k) < brandCounts.size()) ++brandCounts[static_cast<size_t>(k)]; }
  LOG(LINFO, ("CB6-CONVENIENCE-DIAG mwm-collected", "total", pois.size(), "returned", n, "seven", brandCounts[1], "familymart", brandCounts[2], "lawson", brandCounts[3], "seicomart", brandCounts[4], "mybasket", brandCounts[5], "generic", brandCounts[6], "ministop", brandCounts[8], "daily", brandCounts[9]));
  jdoubleArray lats = env->NewDoubleArray(n), lons = env->NewDoubleArray(n), kinds = env->NewDoubleArray(n);
  std::vector<jdouble> la(n), lo(n), ki(n);
  for (jsize i=0;i<n;++i)
  {
    auto const & p=pois[static_cast<size_t>(i)];
    auto const ll=mercator::ToLatLon({p.m_mercatorX,p.m_mercatorY});
    la[i]=ll.m_lat; lo[i]=ll.m_lon; ki[i]=Cb6ConvenienceKind(p.m_identity.m_brand);
  }
  env->SetDoubleArrayRegion(lats,0,n,la.data()); env->SetDoubleArrayRegion(lons,0,n,lo.data());
  env->SetDoubleArrayRegion(kinds,0,n,ki.data());
  env->SetObjectArrayElement(out,0,lats); env->SetObjectArrayElement(out,1,lons); env->SetObjectArrayElement(out,2,kinds);
  return out;
}

JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6ConvenienceMarks(
    JNIEnv * env, jclass, jdoubleArray latsArray, jdoubleArray lonsArray, jintArray kindsArray)
{
  jsize const n = env->GetArrayLength(latsArray);
  LOG(LINFO, ("CB6-CONVENIENCE-DIAG nativeSet-enter", "count", n));
  if (env->GetArrayLength(lonsArray) != n || env->GetArrayLength(kindsArray) != n) { LOG(LINFO, ("CB6-CONVENIENCE-DIAG nativeSet-return", "reason", "array-length-mismatch")); return; }
  jdouble * lats = env->GetDoubleArrayElements(latsArray, nullptr);
  jdouble * lons = env->GetDoubleArrayElements(lonsArray, nullptr);
  jint * kinds = env->GetIntArrayElements(kindsArray, nullptr);
  auto session = frm()->GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CONVENIENCE);
  std::array<size_t, 10> setBrandCounts{}; size_t created = 0;
  for (jsize i = 0; i < n; ++i) { auto const pt = mercator::FromLatLon(lats[i], lons[i]); auto * mark = session.CreateUserMark<Cb6ConvenienceMark>(pt); auto const kind = static_cast<int>(kinds[i]); mark->SetKind(kind); if (kind >= 0 && static_cast<size_t>(kind) < setBrandCounts.size()) ++setBrandCounts[static_cast<size_t>(kind)]; ++created; }
  LOG(LINFO, ("CB6-CONVENIENCE-DIAG marks-created", "count", created, "seven", setBrandCounts[1], "familymart", setBrandCounts[2], "lawson", setBrandCounts[3], "seicomart", setBrandCounts[4], "mybasket", setBrandCounts[5], "generic", setBrandCounts[6], "ministop", setBrandCounts[8], "daily", setBrandCounts[9]));
  session.SetIsVisible(UserMark::Type::CONVENIENCE, true);
  env->ReleaseDoubleArrayElements(latsArray, lats, JNI_ABORT);
  env->ReleaseDoubleArrayElements(lonsArray, lons, JNI_ABORT);
  env->ReleaseIntArrayElements(kindsArray, kinds, JNI_ABORT);
}

'''
if "nativeSetCb6ConvenienceMarks" not in s:
    if anchor not in s: raise SystemExit("Framework JNI anchor missing")
    s = s.replace(anchor, code + anchor, 1)
fw.write_text(s)

java = ROOT / "android/sdk/src/main/java/app/organicmaps/sdk/Framework.java"
s = java.read_text()
anchor = "public class Framework"
# Insert declaration just after class opening to avoid relying on unrelated native methods.
if "nativeSetCb6ConvenienceMarks" not in s:
    pos = s.find("{", s.find(anchor))
    if pos < 0: raise SystemExit("Framework.java class anchor missing")
    decl = "\n  public static native void nativeSetCb6ConvenienceMarks(double[] lats, double[] lons, int[] kinds);\n  public static native double[][] nativeCb6CollectConvenienceMarks(double lat, double lon, int radiusMeters, int scale);\n"
    s = s[:pos+1] + decl + s[pos+1:]
java.write_text(s)

# Pure SVG convenience-brand symbols based on the user-approved reference artwork.
# Deliberately avoid <image>, data:image and embedded raster content because those
# did not render reliably through the CoMaps symbol pipeline.
brand_svg = {
    "cb6-seven": """<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="5" fill="white" stroke="#008044" stroke-width="2"/><path d="M6 5h16l-7 9h-4l5-6H6z" fill="#f58220"/><path d="M16 5h6l-8 10v9h-5v-8z" fill="#e5002b"/><text x="14" y="19" text-anchor="middle" font-family="sans-serif" font-size="5" font-weight="700" fill="#008044">ELEVEN</text></svg>""",
    "cb6-familymart": """<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="4" fill="white" stroke="#009b4d" stroke-width="2"/><rect x="4" y="5" width="20" height="6" rx="1" fill="#009b4d"/><rect x="4" y="12" width="20" height="5" fill="#0086d1"/><text x="14" y="23" text-anchor="middle" font-family="sans-serif" font-size="4.3" font-weight="700" fill="#0072bc">FamilyMart</text></svg>""",
    "cb6-lawson": """<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="4" fill="white" stroke="#1683c9" stroke-width="2"/><path d="M5 7Q14 3 23 7l-2 16Q14 26 7 23z" fill="#1683c9"/><path d="M8 8Q14 6 20 8" fill="none" stroke="white" stroke-width="1"/><text x="14" y="10.5" text-anchor="middle" font-family="sans-serif" font-size="3.4" font-weight="700" fill="white">LAWSON</text><path d="M12 13h4v2h1v7h-6v-7h1z" fill="white"/></svg>""",
    "cb6-seicomart": """<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="5" fill="#f36c21"/><path d="M7 8c3 1 5 0 7-4-1 6 1 9 7 7-3 5-8 8-13 6 3-1 4-3 4-5-2 2-4 1-5-4z" fill="white"/><text x="14" y="23" text-anchor="middle" font-family="sans-serif" font-size="4.1" font-weight="700" fill="white">Seicomart</text></svg>""",
    "cb6-ministop": """<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="5" fill="white" stroke="#c00068" stroke-width="2"/><path d="M5 13l9-8 4 4v-2h3v5c2 0 4 2 4 4 0 3-2 5-5 5H7V12z" fill="none" stroke="#12358b" stroke-width="1.5"/><text x="14" y="16" text-anchor="middle" font-family="sans-serif" font-size="4.5" font-weight="700" fill="#12358b">MINI</text><text x="14" y="21" text-anchor="middle" font-family="sans-serif" font-size="4.5" font-weight="700" fill="#12358b">STOP</text></svg>""",
    "cb6-mybasket": """<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="5" fill="#c40069"/><text x="14" y="11" text-anchor="middle" font-family="sans-serif" font-size="5" fill="white">AEON</text><text x="14" y="19" text-anchor="middle" font-family="sans-serif" font-size="4" font-weight="700" fill="white">まいばすけっと</text></svg>""",
}
fallback = {
    "cb6-convenience": ("CV", "#555555"),
    "cb6-daily": ("D", "#C62828"),
}
for theme in ("light", "dark"):
    d = ROOT / "data/styles/default" / theme / "symbols"
    for name, svg in brand_svg.items():
        if "<image" in svg or "data:image" in svg:
            raise SystemExit("Raster embedding is forbidden in CB6 convenience SVG symbols")
        (d / (name + ".svg")).write_text(svg)
    for name, (label, color) in fallback.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="6" fill="white" stroke="{color}" stroke-width="3"/><text x="14" y="18" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="700" fill="{color}">{label}</text></svg>'''
        (d / (name + ".svg")).write_text(svg)


activity = ROOT / "android/app/src/main/java/app/organicmaps/MwmActivity.java"
a = activity.read_text()
field = "  private Location mCb6ConvenienceLastLocation;\n"
if field not in a:
    pos = a.find("{", a.find("public class MwmActivity extends BaseMwmFragmentActivity"))
    if pos < 0: raise SystemExit("MwmActivity class anchor missing")
    a = a[:pos+1] + "\n" + field + a[pos+1:]
hook = """    if (mCb6ConvenienceLastLocation == null ||
        location.distanceTo(mCb6ConvenienceLastLocation) >= 800.0f)
    {
      final double[][] cb6 = Framework.nativeCb6CollectConvenienceMarks(
          location.getLatitude(), location.getLongitude(), 3000, 17);
      if (cb6 != null && cb6.length == 3 && cb6[0] != null && cb6[1] != null && cb6[2] != null)
      {
        final int n = Math.min(cb6[0].length, Math.min(cb6[1].length, cb6[2].length));
        final double[] lats = java.util.Arrays.copyOf(cb6[0], n);
        final double[] lons = java.util.Arrays.copyOf(cb6[1], n);
        final int[] kinds = new int[n];
        for (int i = 0; i < n; ++i)
          kinds[i] = (int) cb6[2][i];
        android.util.Log.i("CB6-CONVENIENCE-DIAG", "java-transfer count=" + n);
        Framework.nativeSetCb6ConvenienceMarks(lats, lons, kinds);
        mCb6ConvenienceLastLocation = new Location(location);
      }
    }

"""
anchor2 = "    final RoutingController routing = RoutingController.get();\n"
if "nativeCb6CollectConvenienceMarks(" not in a:
    if anchor2 not in a: raise SystemExit("MwmActivity location routing anchor missing")
    a = a.replace(anchor2, hook + anchor2, 1)
activity.write_text(a)

# Suppress only stock vehicle-map convenience presentation. Keep the MWM
# feature, metadata, names and search intact; dedicated CB6 marks own map display.
icons = ROOT / "data/styles/vehicle/include/Icons.mapcss"
style = icons.read_text()
caption_selector = "node|z18-[shop=convenience],\n"
icon_rule = """node|z17-[shop=convenience],
{icon-image: convenience-m.svg; font-size: 13.25;}
"""
size_rule = """node|z18-[shop=convenience],
{font-size: 14.5;}
"""
if style.count(caption_selector) != 2:
    raise SystemExit("Pinned convenience caption selector count changed")
if style.count(icon_rule) != 1:
    raise SystemExit("Pinned convenience icon rule count changed")
if style.count(size_rule) != 1:
    raise SystemExit("Pinned convenience size rule count changed")
style = style.replace(caption_selector, "", 1)
style = style.replace(icon_rule, "", 1)
style = style.replace(size_rule, "", 1)
if "shop=convenience" in style:
    raise SystemExit("Unexpected stock convenience style rule remains")
icons.write_text(style)

print("CB6 dedicated native-MWM convenience collection, renderer, symbols and live-location refresh applied")
