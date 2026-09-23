#!/usr/bin/env python3
from pathlib import Path
import sys, shutil

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
PKG = Path(__file__).resolve().parents[1]

def read(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("missing: " + rel)
    return p.read_text(encoding="utf-8")

def write(rel, s):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")
    print("patched:", rel)

def once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, got {n}")
    return s.replace(old, new, 1)

rel = "android/app/build.gradle"
s = read(rel)
s = once(s, "project.ext.appId = 'app.comaps'", "project.ext.appId = 'jp.cb6.navi'", "appId")
s = once(s, "project.ext.appName = 'CoMaps'", "project.ext.appName = 'CB6 Navi'", "appName")
write(rel, s)

dst = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(PKG / "scripts/Cb6SupplementManager.java", dst)
print("added:", dst.relative_to(ROOT))

rel = "android/app/src/main/res/layout/activity_map.xml"
s = read(rel)
anchor = '''    <include
      layout="@layout/menu"
      android:layout_width="match_parent"
      android:layout_height="wrap_content"
      android:layout_alignParentBottom="true" />'''
addition = anchor + '''
    <TextView
      android:id="@+id/cb6_road_hud"
      android:layout_width="wrap_content"
      android:layout_height="36dp"
      android:layout_alignParentBottom="true"
      android:layout_centerHorizontal="true"
      android:layout_marginBottom="58dp"
      android:background="#CC202020"
      android:ellipsize="end"
      android:gravity="center"
      android:maxLines="1"
      android:minWidth="220dp"
      android:paddingStart="16dp"
      android:paddingEnd="16dp"
      android:text="--------"
      android:textColor="#FFFFFFFF"
      android:textSize="16sp"
      android:textStyle="bold" />
    <TextView
      android:id="@+id/cb6_google_maps"
      android:layout_width="64dp"
      android:layout_height="36dp"
      android:layout_alignParentEnd="true"
      android:layout_alignParentBottom="true"
      android:layout_marginEnd="8dp"
      android:layout_marginBottom="58dp"
      android:background="#CC202020"
      android:gravity="center"
      android:text="Google"
      android:textColor="#FFFFFFFF"
      android:textSize="12sp" />'''
s = once(s, anchor, addition, "activity_map menu")
write(rel, s)

rel = "android/app/src/main/java/app/organicmaps/MwmActivity.java"
s = read(rel)
s = once(s, "import android.widget.Toast;", "import android.widget.Toast;\nimport android.widget.TextView;", "TextView import")
field_anchor = "  private int mNavBarHeight;\n"
field_new = '''  private int mNavBarHeight;
  @Nullable
  private TextView mCb6RoadHud;
  @Nullable
  private TextView mCb6GoogleMaps;
  @Nullable
  private Cb6SupplementManager mCb6SupplementManager;
  private static final int CB6_POSITION_LOWER_DP = 72;
'''
s = once(s, field_anchor, field_new, "fields")
s = once(s, "    initViews(isLaunchByDeepLink);\n    updateViewsInsets();", "    initViews(isLaunchByDeepLink);\n    initCb6Ui();\n    updateViewsInsets();", "init")
s = once(s, "      mMapController.updateMyPositionRoutingOffset(offsetY);", '''      final int cb6LowerPx = Math.round(CB6_POSITION_LOWER_DP
          * getResources().getDisplayMetrics().density);
      mMapController.updateMyPositionRoutingOffset(Math.max(0, offsetY - cb6LowerPx));''', "routing offset")

loc_old = '''    dismissLocationErrorDialog();
    final RoutingController routing = RoutingController.get();
    if (!routing.isNavigating())
      return;

    RoutingInfo info = Framework.nativeGetRouteFollowingInfo();
    routing.updateCachedRoutingInfo(info);
    mNavigationController.update(info);'''
loc_new = '''    dismissLocationErrorDialog();

    if (mCb6SupplementManager != null)
      mCb6SupplementManager.onLocation(location);

    final RoutingController routing = RoutingController.get();
    if (!routing.isNavigating())
    {
      updateCb6RoadHud(Framework.nativeGetAddress(location.getLatitude(), location.getLongitude()));
      return;
    }

    RoutingInfo info = Framework.nativeGetRouteFollowingInfo();
    if (info != null)
      updateCb6RoadHud(info.currentStreet);
    routing.updateCachedRoutingInfo(info);
    mNavigationController.update(info);'''
s = once(s, loc_old, loc_new, "location update")

method_anchor = "  private void onSettingsResult(ActivityResult activityResult)\n"
helpers = '''  private void initCb6Ui()
  {
    mCb6RoadHud = findViewById(R.id.cb6_road_hud);
    mCb6GoogleMaps = findViewById(R.id.cb6_google_maps);
    mCb6SupplementManager = new Cb6SupplementManager(getApplicationContext());

    if (mCb6GoogleMaps != null)
    {
      mCb6GoogleMaps.setOnClickListener(v -> {
        final Location loc = MwmApplication.from(this).getLocationHelper().getSavedLocation();
        final Uri uri;
        if (loc != null)
          uri = Uri.parse("geo:" + loc.getLatitude() + "," + loc.getLongitude() + "?q=" + loc.getLatitude() + "," + loc.getLongitude());
        else
          uri = Uri.parse("geo:0,0?q=");
        final Intent intent = new Intent(Intent.ACTION_VIEW, uri);
        intent.setPackage("com.google.android.apps.maps");
        try { startActivity(intent); }
        catch (Exception e) { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
      });
    }
  }

  private void updateCb6RoadHud(@Nullable String raw)
  {
    if (mCb6RoadHud == null) return;
    String value = raw == null ? "" : raw.trim();
    if (value.isEmpty()) { mCb6RoadHud.setText("--------"); return; }
    String[] parts = value.split(",");
    String best = "";
    for (String part : parts)
    {
      String p = part.trim();
      if (p.isEmpty()) continue;
      String lower = p.toLowerCase(java.util.Locale.ROOT);
      if (p.contains("国道") || p.contains("道道") || p.contains("県道") || p.contains("市道") || p.contains("通") || p.contains("線") || lower.contains("road") || lower.contains("street")) { best = p; break; }
      if (best.isEmpty() || p.length() < best.length()) best = p;
    }
    if (best.isEmpty()) best = value;
    if (best.length() > 42) best = best.substring(0, 42);
    mCb6RoadHud.setText(best);
  }

'''
s = once(s, method_anchor, helpers + method_anchor, "helper methods")
write(rel, s)

rel = "android/sdk/src/main/java/app/organicmaps/sdk/Framework.java"
s = read(rel)
decl = "  public static native String nativeGetAddress(double lat, double lon);\n"
s = once(s, decl, decl + '''
  // CB6 supplemental marks. Arrays must have identical lengths.
  public static native void nativeSetCb6DrivingMarks(double[] lat, double[] lon, int[] kind);
''', "Framework declaration")
write(rel, s)

rel = "libs/map/user_mark.hpp"
s = read(rel)
s = once(s, "    COLORED,\n    TRAFFIC_LIGHT,\n    USER_MARK_TYPES_COUNT,", "    COLORED,\n    TRAFFIC_LIGHT,\n    CB6_DRIVING,\n    USER_MARK_TYPES_COUNT,", "mark enum")
class_anchor = "class DebugMarkPoint : public UserMark\n"
cb6_class = '''class Cb6DrivingMark : public UserMark
{
public:
  explicit Cb6DrivingMark(m2::PointD const & ptOrg);
  void SetKind(int kind);
  drape_ptr<SymbolNameZoomInfo> GetSymbolNames() const override;
  uint16_t GetPriority() const override;
  int GetMinZoom() const override;
  bool SymbolIsPOI() const override { return true; }
  bool IsNonDisplaceable() const override { return true; }
  bool GetDepthTestEnabled() const override { return false; }
private:
  int m_kind = 6;
};

'''
s = once(s, class_anchor, cb6_class + class_anchor, "Cb6DrivingMark declaration")
write(rel, s)

rel = "libs/map/user_mark.cpp"
s = read(rel)
impl_anchor = "DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg) : UserMark(ptOrg, UserMark::Type::DEBUG_MARK) {}\n"
impl = '''Cb6DrivingMark::Cb6DrivingMark(m2::PointD const & ptOrg)
  : UserMark(ptOrg, UserMark::Type::CB6_DRIVING)
{}
void Cb6DrivingMark::SetKind(int kind) { m_kind = kind; SetDirty(); }
drape_ptr<df::UserPointMark::SymbolNameZoomInfo> Cb6DrivingMark::GetSymbolNames() const
{
  auto symbols = make_unique_dp<SymbolNameZoomInfo>();
  switch (m_kind)
  {
  case 0: symbols->insert({15, "cb6-stop"}); symbols->insert({17, "cb6-stop-l"}); break;
  case 1: symbols->insert({13, "cb6-seven"}); break;
  case 2: symbols->insert({13, "cb6-familymart"}); break;
  case 3: symbols->insert({13, "cb6-lawson"}); break;
  case 4: symbols->insert({13, "cb6-seicomart"}); break;
  case 5: symbols->insert({13, "cb6-mybasket"}); break;
  case 7: symbols->insert({14, "cb6-signal"}); symbols->insert({17, "cb6-signal-l"}); break;
  case 8: symbols->insert({13, "cb6-ministop"}); break;
  case 9: symbols->insert({13, "cb6-daily"}); break;
  default: symbols->insert({13, "cb6-convenience"}); break;
  }
  return symbols;
}
uint16_t Cb6DrivingMark::GetPriority() const
{
  if (m_kind == 7) return static_cast<uint16_t>(UserMark::Priority::TrafficLight);
  if (m_kind == 0) return static_cast<uint16_t>(UserMark::Priority::RoadWarning);
  return static_cast<uint16_t>(UserMark::Priority::Default);
}
int Cb6DrivingMark::GetMinZoom() const
{
  if (m_kind == 7) return 14;
  if (m_kind == 0) return 15;
  return 13;
}

'''
s = once(s, impl_anchor, impl + impl_anchor, "Cb6DrivingMark implementation")
s = once(s, '  case UserMark::Type::TRAFFIC_LIGHT: return "TRAFFIC_LIGHT";', '  case UserMark::Type::TRAFFIC_LIGHT: return "TRAFFIC_LIGHT";\n  case UserMark::Type::CB6_DRIVING: return "CB6_DRIVING";', "DebugPrint")
write(rel, s)

rel = "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = read(rel)
jni_anchor = '''JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeClearApiPoints(JNIEnv * env, jclass clazz)
{
  frm()->GetBookmarkManager().GetEditSession().ClearGroup(UserMark::Type::API);
}
'''
jni_new = jni_anchor + '''
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6DrivingMarks(JNIEnv * env, jclass, jdoubleArray latArray, jdoubleArray lonArray, jintArray kindArray)
{
  if (latArray == nullptr || lonArray == nullptr || kindArray == nullptr) return;
  jsize const n = env->GetArrayLength(latArray);
  if (env->GetArrayLength(lonArray) != n || env->GetArrayLength(kindArray) != n) return;
  jdouble * lats = env->GetDoubleArrayElements(latArray, nullptr);
  jdouble * lons = env->GetDoubleArrayElements(lonArray, nullptr);
  jint * kinds = env->GetIntArrayElements(kindArray, nullptr);
  if (lats == nullptr || lons == nullptr || kinds == nullptr)
  {
    if (lats != nullptr) env->ReleaseDoubleArrayElements(latArray, lats, JNI_ABORT);
    if (lons != nullptr) env->ReleaseDoubleArrayElements(lonArray, lons, JNI_ABORT);
    if (kinds != nullptr) env->ReleaseIntArrayElements(kindArray, kinds, JNI_ABORT);
    return;
  }
  {
    auto session = frm()->GetBookmarkManager().GetEditSession();
    session.ClearGroup(UserMark::Type::CB6_DRIVING);
    for (jsize i = 0; i < n; ++i)
    {
      if (lats[i] < -90.0 || lats[i] > 90.0 || lons[i] < -180.0 || lons[i] > 180.0) continue;
      auto * mark = session.CreateUserMark<Cb6DrivingMark>(mercator::FromLatLon(lats[i], lons[i]));
      mark->SetKind(static_cast<int>(kinds[i]));
    }
  }
  env->ReleaseDoubleArrayElements(latArray, lats, JNI_ABORT);
  env->ReleaseDoubleArrayElements(lonArray, lons, JNI_ABORT);
  env->ReleaseIntArrayElements(kindArray, kinds, JNI_ABORT);
}
'''
s = once(s, jni_anchor, jni_new, "CB6 JNI")
write(rel, s)

rel = "data/styles/vehicle/include/Icons.mapcss"
s = read(rel)
s += '''

/* CB6 native MWM traffic signal fallback. */
node|z19-[highway=traffic_signals]
{icon-image: traffic_signals.svg;}
'''
write(rel, s)

rel = "data/styles/vehicle/include/Basemap.mapcss"
s = read(rel)
s += '''

/* CB6 suppress buildings strongly in vehicle mode. */
area|z15-[building],
area|z16-[building],
area|z16-[building:part]
{fill-opacity:0.08;}
'''
write(rel, s)

rel = "data/styles/vehicle/include/Basemap_label.mapcss"
s = read(rel)
s += '''

/* CB6 suppress house-number / fine-block clutter. */
area|z1-[building][addr:housenumber]
{text:none;}

node|z13-[place=locality],
node|z13-[place=locality]::int_name,
node|z13-[place=quarter],
node|z13-[place=quarter]::int_name,
node|z13-[place=neighbourhood],
node|z13-[place=neighbourhood]::int_name
{text:none;}
'''
write(rel, s)

for theme in ("light", "dark"):
    src = PKG / "icons" / theme
    dst = ROOT / "data/styles/default" / theme / "symbols"
    for p in src.glob("*.svg"):
        shutil.copy2(p, dst / p.name)
        print("icon:", (dst / p.name).relative_to(ROOT))

print("CB6 Navi Complete patch applied.")