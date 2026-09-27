#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

root = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parents[2]
cpp = root / "android/sdk/src/main/cpp"
sdk = cpp / "app/organicmaps/sdk"
cmake = cpp / "CMakeLists.txt"
java = root / "android/sdk/src/main/java/app/organicmaps/sdk/Framework.java"

for src in ("convenience_brand_classifier.hpp","convenience_brand_classifier.cpp",
            "convenience_mwm_collector.hpp","convenience_mwm_collector.cpp"):
    shutil.copy2(repo / "v2/poi/native" / src, sdk / src)

cm = cmake.read_text()
anchor = "  app/organicmaps/sdk/Framework.cpp\n"
addition = ("  app/organicmaps/sdk/convenience_brand_classifier.cpp\n"
            "  app/organicmaps/sdk/convenience_mwm_collector.cpp\n")
if addition not in cm:
    if anchor not in cm: raise SystemExit("CB6 convenience diagnostic: CMake anchor missing")
    cm = cm.replace(anchor, anchor + addition, 1)
cmake.write_text(cm)

fw = (sdk / "Framework.cpp").read_text()
inc = '#include "app/organicmaps/sdk/convenience_mwm_collector.hpp"\n'
if inc not in fw:
    fw = fw.replace('#include "app/organicmaps/sdk/Framework.hpp"\n',
                    '#include "app/organicmaps/sdk/Framework.hpp"\n' + inc, 1)

jni = r'''
extern "C" JNIEXPORT jobjectArray JNICALL
Java_app_organicmaps_sdk_Framework_nativeCb6ConvenienceDiagnostic(JNIEnv * env, jclass, jdouble lat, jdouble lon,
                                                                  jint radiusMeters, jint scale)
{
  if (!g_framework || radiusMeters <= 0)
    return env->NewObjectArray(0, env->FindClass("java/lang/String"), nullptr);

  auto const center = mercator::FromLatLon(lat, lon);
  auto const delta = mercator::MetersToMercator(radiusMeters);
  m2::RectD const rect(center.x - delta, center.y - delta, center.x + delta, center.y + delta);
  auto const pois = cb6::poi::CollectConveniencePois(frm()->GetDataSource(), rect, scale);

  jclass const stringClass = env->FindClass("java/lang/String");
  auto const count = static_cast<jsize>(std::min<size_t>(pois.size(), 200));
  jobjectArray out = env->NewObjectArray(count, stringClass, nullptr);
  for (jsize i = 0; i < count; ++i)
  {
    auto const & p = pois[static_cast<size_t>(i)];
    auto const ll = mercator::ToLatLon({p.m_mercatorX, p.m_mercatorY});
    std::string row = std::string(cb6::poi::DebugPrint(p.m_identity.m_brand)) + "|" +
                      p.m_identity.m_evidenceSource + "|" + std::to_string(ll.m_lat) + "|" +
                      std::to_string(ll.m_lon);
    jstring s = env->NewStringUTF(row.c_str());
    env->SetObjectArrayElement(out, i, s);
    env->DeleteLocalRef(s);
  }
  return out;
}
'''
if "nativeCb6ConvenienceDiagnostic" not in fw:
    fw += "\n" + jni
(sdk / "Framework.cpp").write_text(fw)

j = java.read_text()
decl = "  public static native String[] nativeCb6ConvenienceDiagnostic(double lat, double lon, int radiusMeters, int scale);\n"
if decl not in j:
    pos = j.rfind("}")
    if pos < 0: raise SystemExit("CB6 convenience diagnostic: Java class end missing")
    j = j[:pos] + decl + j[pos:]
java.write_text(j)
print("CB6 convenience diagnostic native bridge applied")
