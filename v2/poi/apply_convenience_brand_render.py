#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

# Dedicated ownership: never reuse traffic-light / CB6 driving mark groups.
uh = ROOT / "libs/map/user_mark.hpp"
s = uh.read_text()
old = "    TRAFFIC_LIGHT,\n    USER_MARK_TYPES_COUNT,"
new = "    TRAFFIC_LIGHT,\n    CONVENIENCE,\n    USER_MARK_TYPES_COUNT,"
if "    CONVENIENCE," not in s:
    if old not in s: raise SystemExit("UserMark type anchor missing")
    s = s.replace(old, new, 1)
uh.write_text(s)

fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text()
anchor = "JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeClearApiPoints"
code = r'''
class Cb6ConvenienceMark final : public UserMark
{
public:
  Cb6ConvenienceMark(m2::PointD const & pt, int kind) : UserMark(pt, UserMark::Type::CONVENIENCE), m_kind(kind) {}

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
    symbols->insert({12, symbol});
    return symbols;
  }
  int GetMinZoom() const override { return 12; }
  bool SymbolIsPOI() const override { return true; }
  bool IsNonDisplaceable() const override { return false; }
  bool GetDepthTestEnabled() const override { return false; }

private:
  int m_kind;
};

JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6ConvenienceMarks(
    JNIEnv * env, jclass, jdoubleArray latsArray, jdoubleArray lonsArray, jintArray kindsArray)
{
  jsize const n = env->GetArrayLength(latsArray);
  if (env->GetArrayLength(lonsArray) != n || env->GetArrayLength(kindsArray) != n)
    return;
  jdouble * lats = env->GetDoubleArrayElements(latsArray, nullptr);
  jdouble * lons = env->GetDoubleArrayElements(lonsArray, nullptr);
  jint * kinds = env->GetIntArrayElements(kindsArray, nullptr);
  auto session = frm()->GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CONVENIENCE);
  for (jsize i = 0; i < n; ++i)
  {
    auto const pt = mercator::FromLatLon(lats[i], lons[i]);
    session.CreateUserMark<Cb6ConvenienceMark>(pt, static_cast<int>(kinds[i]));
  }
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
    decl = "\n  public static native void nativeSetCb6ConvenienceMarks(double[] lats, double[] lons, int[] kinds);\n"
    s = s[:pos+1] + decl + s[pos+1:]
java.write_text(s)

# Generate simple original CB6 symbols. No third-party logo artwork is embedded.
brands = {
 "cb6-convenience": ("CV", "#555555"),
 "cb6-seven": ("7", "#2E7D32"),
 "cb6-familymart": ("F", "#1683C4"),
 "cb6-lawson": ("L", "#1976D2"),
 "cb6-seicomart": ("S", "#F57C00"),
 "cb6-mybasket": ("M", "#8E24AA"),
 "cb6-ministop": ("Mi", "#1565C0"),
 "cb6-daily": ("D", "#C62828"),
}
for theme in ("light", "dark"):
    d = ROOT / "data/styles/default" / theme / "symbols"
    for name, (label, color) in brands.items():
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
<rect x="1" y="1" width="26" height="26" rx="6" fill="white" stroke="{color}" stroke-width="3"/>
<text x="14" y="18" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="700" fill="{color}">{label}</text>
</svg>"""
        (d / (name + ".svg")).write_text(svg)

print("CB6 dedicated convenience UserMark type, JNI renderer and original symbols applied")
