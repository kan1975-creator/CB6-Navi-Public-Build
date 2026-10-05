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

# Exact six approved brand assets keep their original embedded PNG bytes, but
# CoMaps' stock skin_generator consumes those bytes through its native PNG path.
# No SVG <image> rendering is used for these six symbols.
CB6_DIRECT_PNG_ALLOWLIST = frozenset({
    "cb6-seven.png", "cb6-familymart.png", "cb6-lawson.png",
    "cb6-seicomart.png", "cb6-ministop.png", "cb6-mybasket.png",
})

def cb6_extract_approved_png(svg_filename, svg):
    import base64, re
    png_filename = svg_filename[:-4] + ".png"
    if png_filename not in CB6_DIRECT_PNG_ALLOWLIST:
        raise ValueError("Direct PNG is forbidden outside exact CB6 allowlist: " + png_filename)
    matches = re.findall(r'href="data:image/png;base64,([^"]+)"', svg)
    if len(matches) != 1:
        raise ValueError("Approved CB6 source must contain exactly one embedded PNG: " + svg_filename)
    png = base64.b64decode(matches[0], validate=True)
    if not png.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
        raise ValueError("Approved CB6 payload is not PNG: " + svg_filename)
    return png_filename, png

brand_png = {}
for png_filename in sorted(CB6_DIRECT_PNG_ALLOWLIST):
    svg_filename = png_filename[:-4] + ".svg"
    source = Path(__file__).resolve().parent / svg_filename
    if not source.is_file():
        raise FileNotFoundError("Approved CB6 convenience source missing: " + svg_filename)
    extracted_name, png = cb6_extract_approved_png(svg_filename, source.read_text())
    if extracted_name != png_filename:
        raise ValueError("Approved CB6 PNG name changed: " + svg_filename)
    brand_png[png_filename] = png

fallback = {"cb6-convenience": ("CV", "#555555"), "cb6-daily": ("D", "#C62828")}
for theme in ("light", "dark"):
    style_root = ROOT / "data/styles/default" / theme
    symbols = style_root / "symbols"
    for png_filename, png in brand_png.items():
        for density in ("mdpi", "hdpi", "xhdpi", "6plus", "xxhdpi", "xxxhdpi"):
            (style_root / density / png_filename).write_bytes(png)
    for name, (label, color) in fallback.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="6" fill="white" stroke="{color}" stroke-width="3"/><text x="14" y="18" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="700" fill="{color}">{label}</text></svg>'''
        (symbols / (name + ".svg")).write_text(svg)


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
