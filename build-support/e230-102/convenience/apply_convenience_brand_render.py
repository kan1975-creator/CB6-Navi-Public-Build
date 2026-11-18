#!/usr/bin/env python3
from pathlib import Path
from io import BytesIO
import shutil, sys

from PIL import Image

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
REPO = Path(__file__).resolve().parent
sdk = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk"
for src in ("convenience_brand_classifier.hpp","convenience_brand_classifier.cpp",
            "convenience_mwm_collector.hpp","convenience_mwm_collector.cpp"):
    shutil.copy2(REPO / "native" / src, sdk / src)
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
signal_new = "    TRAFFIC_LIGHT,\n    CB6_SIGNAL,\n    CONVENIENCE,\n    USER_MARK_TYPES_COUNT,"
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
extra_inc = '#include <map>\n#include <tuple>\n#include <chrono>\n'
if extra_inc not in s:
    s = s.replace('#include "app/organicmaps/sdk/Framework.hpp"\n',
                  '#include "app/organicmaps/sdk/Framework.hpp"\n' + extra_inc, 1)
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
    // CB6 relative boundary adjustment: keep the proven CoMaps UserMark
    // selection mechanism and move the existing size stages one zoom farther out.
    symbols->insert({14, std::string(symbol) + "-50"});
    symbols->insert({15, std::string(symbol) + "-85"});
    symbols->insert({16, symbol});
    return symbols;
  }
  int GetMinZoom() const override { return 14; }
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
  auto const n = static_cast<jsize>(pois.size());
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
  // Append-only convenience marks: keep IDs until application shutdown.
  using ShopKey = std::tuple<double, double, int>;
  static std::map<ShopKey, kml::MarkId> shopMarks;
  static decltype(&frm()->GetBookmarkManager()) owner = nullptr;
  auto * currentManager = &frm()->GetBookmarkManager();
  if (owner != currentManager)
  {
    shopMarks.clear();  // Never reuse IDs from a different BookmarkManager.
    owner = currentManager;
  }
  if (n > 0)
  {
    auto session = currentManager->GetEditSession();
    size_t added = 0, kept = 0;
    for (jsize i = 0; i < n; ++i)
    {
      ShopKey const key{lats[i], lons[i], static_cast<int>(kinds[i])};
      if (shopMarks.find(key) != shopMarks.end())
      {
        ++kept;
        continue;
      }
      auto * mark = session.CreateUserMark<Cb6ConvenienceMark>(
          mercator::FromLatLon(std::get<0>(key), std::get<1>(key)));
      mark->SetKind(std::get<2>(key));
      shopMarks.emplace(key, mark->GetId());
      ++added;
    }
    session.SetIsVisible(UserMark::Type::CONVENIENCE, true);
    LOG(LINFO, ("CB6-CONVENIENCE-DIAG append-only", "added", added,
                "kept", kept, "total", shopMarks.size()));
  }
  else
  {
    LOG(LINFO, ("CB6-CONVENIENCE-DIAG keep-on-empty", "total", shopMarks.size()));
  }
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
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Approved CB6 payload is not PNG: " + svg_filename)
    return png_filename, png

brand_png = {}
for png_filename in sorted(CB6_DIRECT_PNG_ALLOWLIST):
    svg_filename = png_filename[:-4] + ".svg"
    source = Path(__file__).resolve().parent / "assets" / svg_filename
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
    density_long_edges = {
        "mdpi": 22, "hdpi": 32, "xhdpi": 43,
        "6plus": 52, "xxhdpi": 65, "xxxhdpi": 77,
    }
    for png_filename, png in brand_png.items():
        with Image.open(BytesIO(png)) as source_image:
            source_image.load()
            source_width, source_height = source_image.size
            source_long_edge = max(source_width, source_height)
            for density, target_long_edge in density_long_edges.items():
                scale = target_long_edge / source_long_edge
                target_size = (
                    max(1, round(source_width * scale)),
                    max(1, round(source_height * scale)),
                )
                density_dir = style_root / density
                density_dir.mkdir(parents=True, exist_ok=True)
                output = BytesIO()
                source_image.resize(target_size, Image.Resampling.LANCZOS).save(output, format="PNG")
                (density_dir / png_filename).write_bytes(output.getvalue())
                for suffix, ratio in (("-85", 0.85), ("-50", 0.50)):
                    variant_size = (
                        max(1, round(target_size[0] * ratio)),
                        max(1, round(target_size[1] * ratio)),
                    )
                    variant = BytesIO()
                    source_image.resize(variant_size, Image.Resampling.LANCZOS).save(variant, format="PNG")
                    variant_name = png_filename[:-4] + suffix + ".png"
                    (density_dir / variant_name).write_bytes(variant.getvalue())
    for name, (label, color) in fallback.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="1" y="1" width="26" height="26" rx="6" fill="white" stroke="{color}" stroke-width="3"/><text x="14" y="18" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="700" fill="{color}">{label}</text></svg>'''
        (symbols / (name + ".svg")).write_text(svg)
        for suffix, ratio in (("-85", 0.85), ("-50", 0.50)):
            side = max(1, round(28 * ratio))
            scaled = svg.replace('width="28" height="28"', f'width="{side}" height="{side}"')
            (symbols / (name + suffix + ".svg")).write_text(scaled)


activity = ROOT / "android/app/src/main/java/app/organicmaps/MwmActivity.java"
a = activity.read_text()
field = """  private Location mCb6ConvenienceLastLocation;
"""
if field not in a:
    pos = a.find("{", a.find("public class MwmActivity extends BaseMwmFragmentActivity"))
    if pos < 0: raise SystemExit("MwmActivity class anchor missing")
    a = a[:pos+1] + "\n" + field + a[pos+1:]
hook = """    if (mCb6ConvenienceLastLocation == null ||
        location.distanceTo(mCb6ConvenienceLastLocation) >= 800.0f)
    {
      cb6ScheduleConvenienceViewportRefresh();
      mCb6ConvenienceLastLocation = new Location(location);
    }

"""
anchor2 = "    final RoutingController routing = RoutingController.get();\n"
if "nativeCb6CollectConvenienceMarks(" not in a:
    if anchor2 not in a: raise SystemExit("MwmActivity location routing anchor missing")
    a = a.replace(anchor2, hook + anchor2, 1)

activity.write_text(a)

# Refresh the dedicated offline marks after a settled map gesture, not only GPS.
# MapView's ACTION_UP is the input event, not an assertion that map animation ended.
view = ROOT / "android/sdk/src/main/java/app/organicmaps/sdk/MapView.java"
v = view.read_text()
view_anchor = "    Map.onTouch(action, event, pointerIndex);\n"
view_hook = """    Map.onTouch(action, event, pointerIndex);
    if ((event.getActionMasked() == MotionEvent.ACTION_UP ||
         event.getActionMasked() == MotionEvent.ACTION_CANCEL) && mCb6OnGestureEnd != null)
      mCb6OnGestureEnd.run();
"""
if "mCb6OnGestureEnd" not in v:
    if v.count(view_anchor) != 1:
        raise SystemExit("MapView touch anchor missing")
    class_anchor = "public class MapView extends SurfaceView\n{\n"
    if v.count(class_anchor) != 1:
        raise SystemExit("MapView class anchor missing")
    v = v.replace(class_anchor, class_anchor + """  private static Runnable mCb6OnGestureEnd;
  public static void setCb6OnGestureEnd(Runnable listener)
  {
    mCb6OnGestureEnd = listener;
  }

""", 1)
    v = v.replace(view_anchor, view_hook, 1)
view.write_text(v)

a = activity.read_text()
gesture_field = """  // CoMaps DataSource is NOT accessed from the worker: only array conversion is.
  private java.util.concurrent.ExecutorService mCb6ConvenienceTransform =
      java.util.concurrent.Executors.newSingleThreadExecutor();
  private final java.util.concurrent.atomic.AtomicInteger mCb6ConvenienceGeneration =
      new java.util.concurrent.atomic.AtomicInteger();
  private boolean mCb6ConveniencePaused = true;
  // Cached successful native collection footprints. Radius 3500m permits a
  // 500m center shift while covering the original 3000m requested area.
  private final java.util.ArrayList<double[]> mCb6ConvenienceCovered =
      new java.util.ArrayList<>();
  private boolean cb6ConvenienceAlreadyCovered(double lat, double lon, int scale)
  {
    final float[] distance = new float[1];
    for (double[] c : mCb6ConvenienceCovered)
    {
      if ((int)c[2] != scale) continue;
      android.location.Location.distanceBetween(lat, lon, c[0], c[1], distance);
      if (distance[0] <= 500.0f) return true;
    }
    return false;
  }
  private void cb6ConvenienceRememberCovered(double lat, double lon, int scale)
  {
    if (cb6ConvenienceAlreadyCovered(lat, lon, scale)) return;
    // Bounded cache, mark retention itself is not bounded or altered.
    if (mCb6ConvenienceCovered.size() >= 128)
      mCb6ConvenienceCovered.remove(0);
    mCb6ConvenienceCovered.add(new double[] {lat, lon, scale});
  }
  private double[] mCb6ConvenienceLastSample;
  private int mCb6ConvenienceStableSamples;
  private final Runnable mCb6ConvenienceSettlePoll = new Runnable()
  {
    @Override public void run()
    {
      if (mCb6ConveniencePaused || !cb6ConvenienceRenderingActive()) return;
      final double[] center = Framework.nativeGetScreenRectCenter();
      if (center == null || center.length != 2)
      {
        mCb6ConvenienceLastSample = null;
        mCb6ConvenienceStableSamples = 0;
        mCb6ConvenienceHandler.postDelayed(this, 180);
        return;
      }
      final int scale = Framework.nativeGetDrawScale();
      if (scale < 14)
      {
        mCb6ConvenienceLastSample = null;
        mCb6ConvenienceStableSamples = 0;
        return;
      }
      final double[] now = new double[] {center[0], center[1], scale};
      if (mCb6ConvenienceLastSample != null &&
          Math.abs(now[0] - mCb6ConvenienceLastSample[0]) < 1e-7 &&
          Math.abs(now[1] - mCb6ConvenienceLastSample[1]) < 1e-7 &&
          now[2] == mCb6ConvenienceLastSample[2])
        ++mCb6ConvenienceStableSamples;
      else
        mCb6ConvenienceStableSamples = 0;
      mCb6ConvenienceLastSample = now;
      if (mCb6ConvenienceStableSamples >= 2)
      {
        cb6CollectConvenienceSafely(now[0], now[1], scale);
        return;
      }
      mCb6ConvenienceHandler.postDelayed(this, 180);
    }
  };
  private void cb6ScheduleConvenienceViewportRefresh()
  {
    if (mCb6ConveniencePaused) return;
    mCb6ConvenienceGeneration.incrementAndGet();
    mCb6ConvenienceHandler.removeCallbacks(mCb6ConvenienceSettlePoll);
    mCb6ConvenienceLastSample = null;
    mCb6ConvenienceStableSamples = 0;
    mCb6ConvenienceHandler.postDelayed(mCb6ConvenienceSettlePoll, 180);
  }
  private void cb6CollectConvenienceSafely(final double lat, final double lon, final int scale)
  {
    if (mCb6ConveniencePaused || !cb6ConvenienceRenderingActive()) return;
    if (cb6ConvenienceAlreadyCovered(lat, lon, scale)) return;
    final int generation = mCb6ConvenienceGeneration.get();
    // JNI DataSource collection remains on main thread pending thread-safety proof.
    // The 500m overlap margin is required for safe viewport coverage reuse.
    final double[][] cb6 = Framework.nativeCb6CollectConvenienceMarks(lat, lon, 3500, scale);
    if (cb6 == null || cb6.length != 3 || cb6[0] == null || cb6[1] == null || cb6[2] == null)
      return;
    final int n = Math.min(cb6[0].length, Math.min(cb6[1].length, cb6[2].length));
    try
    {
      mCb6ConvenienceTransform.execute(() ->
      {
        final double[] lats = java.util.Arrays.copyOf(cb6[0], n);
        final double[] lons = java.util.Arrays.copyOf(cb6[1], n);
        final int[] kinds = new int[n];
        for (int i = 0; i < n; ++i) kinds[i] = (int) cb6[2][i];
        mCb6ConvenienceHandler.post(() ->
        {
          if (mCb6ConveniencePaused || generation != mCb6ConvenienceGeneration.get() ||
              !cb6ConvenienceRenderingActive()) return;
          Framework.nativeSetCb6ConvenienceMarks(lats, lons, kinds);
          // Empty MWM results may be transient: do not cache them as coverage.
          if (n > 0)
            cb6ConvenienceRememberCovered(lat, lon, scale);
        });
      });
    }
    catch (java.util.concurrent.RejectedExecutionException ignored)
    {
      // The activity was paused and the worker was shut down.
    }
  }
  private boolean cb6ConvenienceRenderingActive()
  {
    return mMapController != null && mMapController.isRenderingActive();
  }
  private final android.os.Handler mCb6ConvenienceHandler =
      new android.os.Handler(android.os.Looper.getMainLooper());
  private final Runnable mCb6ConvenienceGestureEnd = () ->
  {
    cb6ScheduleConvenienceViewportRefresh();
  };
"""
if "mCb6ConvenienceGestureEnd" not in a:
    if a.count(field) != 1:
        raise SystemExit("Convenience field anchor missing")
    a = a.replace(field, field + gesture_field, 1)
    resume = "  protected void onResume()\n  {\n    super.onResume();\n"
    pause = "  protected void onPause()\n  {\n"
    if a.count(resume) != 1 or a.count(pause) != 1:
        raise SystemExit("Activity lifecycle anchor missing")
    a = a.replace(resume, resume + """    if (mCb6ConvenienceTransform.isShutdown())
      mCb6ConvenienceTransform = java.util.concurrent.Executors.newSingleThreadExecutor();
    mCb6ConveniencePaused = false;
    app.organicmaps.sdk.MapView.setCb6OnGestureEnd(mCb6ConvenienceGestureEnd);
    mCb6ConvenienceGestureEnd.run();
""", 1)
    a = a.replace(pause, pause + """    mCb6ConveniencePaused = true;
    mCb6ConvenienceGeneration.incrementAndGet();
    mCb6ConvenienceHandler.removeCallbacks(mCb6ConvenienceSettlePoll);
    mCb6ConvenienceTransform.shutdownNow();
    app.organicmaps.sdk.MapView.setCb6OnGestureEnd(null);
""", 1)
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
