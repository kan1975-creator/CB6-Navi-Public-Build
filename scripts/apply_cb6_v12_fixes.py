#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()


def read(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("missing: " + rel)
    return p.read_text(encoding="utf-8")


def write(rel, s):
    p = ROOT / rel
    p.write_text(s, encoding="utf-8")
    print("v1.2 patched:", rel)


def once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, got {n}")
    return s.replace(old, new, 1)

# 1) Road HUD: do not depend on a nearby building address.
# Pick the nearest named highway feature around the GPS point, then fall back to reverse-geocoder address.
rel = "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = read(rel)
inc_anchor = '#include "indexer/feature_altitude.hpp"\n'
extra_includes = (
    '#include "indexer/classificator.hpp"\n'
    '#include "indexer/data_source_helpers.hpp"\n'
    '#include "indexer/feature_algo.hpp"\n'
)
if extra_includes not in s:
    s = once(s, inc_anchor, inc_anchor + extra_includes, "nearest-road includes")

old = '''JNIEXPORT jstring JNICALL Java_app_organicmaps_sdk_Framework_nativeGetStreetName(JNIEnv * env, jclass clazz,
                                                                                 jdouble lat, jdouble lon)
{
  auto const info = frm()->GetAddressAtPoint(mercator::FromLatLon(lat, lon));
  return jni::ToJavaString(env, info.GetStreetName());
}
'''
new = '''JNIEXPORT jstring JNICALL Java_app_organicmaps_sdk_Framework_nativeGetStreetName(JNIEnv * env, jclass clazz,
                                                                                 jdouble lat, jdouble lon)
{
  auto const point = mercator::FromLatLon(lat, lon);
  std::string bestName;
  double bestDistanceMeters = 1.0e9;

  indexer::ForEachFeatureAtPoint(frm()->GetDataSource(), [&](FeatureType & ft)
  {
    if (ft.GetGeomType() != feature::GeomType::Line)
      return;

    bool isRoad = false;
    ft.ForEachType([&](uint32_t type)
    {
      auto const typeName = classif().GetReadableObjectName(type);
      if (typeName.rfind("highway-", 0) == 0)
        isRoad = true;
    });
    if (!isRoad)
      return;

    std::string name(ft.GetName(localisation::kDefaultNameIndex));
    if (name.empty())
      name = ft.GetTranslatedName().m_primary.value_or(std::string());
    if (name.empty())
      return;

    auto const distanceMeters = feature::GetMinDistanceMeters(ft, point);
    if (distanceMeters < bestDistanceMeters)
    {
      bestDistanceMeters = distanceMeters;
      bestName = name;
    }
  }, point, 35.0 /* toleranceInMeters */);

  if (bestName.empty())
  {
    auto const info = frm()->GetAddressAtPoint(point);
    bestName = info.GetStreetName();
  }

  return jni::ToJavaString(env, bestName);
}
'''
s = once(s, old, new, "nearest-road JNI implementation")
write(rel, s)

# 2) Fine Japanese address/block labels.
# v1.1 changed only three style directories. CoMaps can switch/derive several styles,
# so apply the suppression to every style that actually owns Basemap_label.mapcss.
suppress_marker = "CB6 v1.2: suppress fine address/block labels in every map style"
suppress = '''\n\n/* CB6 v1.2: suppress fine address/block labels in every map style. */
node|z10-[place=suburb],
area|z10-[place=suburb],
node|z12-[place=locality],
area|z12-[place=locality],
node|z12-[place=quarter],
area|z12-[place=quarter],
node|z12-[place=neighbourhood],
area|z12-[place=neighbourhood]
{text:none;}
'''
style_count = 0
for p in sorted((ROOT / "data/styles").glob("*/include/Basemap_label.mapcss")):
    s = p.read_text(encoding="utf-8")
    if suppress_marker not in s:
        s += suppress
        p.write_text(s, encoding="utf-8")
    style_count += 1
    print("v1.2 address style:", p.relative_to(ROOT))
if style_count < 3:
    raise SystemExit(f"unexpected Basemap_label style count: {style_count}")

# 3) Parking density: at the real-device 100 m view, individual P marks obscure the map.
# Delay parking nodes to z19 and require generous icon spacing; keep parking area geometry intact.
parking_marker = "CB6 v1.2: reduce individual parking icon density"
parking_count = 0
for p in sorted((ROOT / "data/styles").glob("*/include/Icons.mapcss")):
    s = p.read_text(encoding="utf-8")
    # Only alter the parking selector line, not charging stations/car pooling grouped with it.
    s = re.sub(r"node\|z(?:1[0-8])-(\[amenity=parking\])", r"node|z19-\1", s)
    if parking_marker not in s:
        s += '''\n\n/* CB6 v1.2: reduce individual parking icon density at normal driving zooms. */
node|z19-[amenity=parking]
{icon-min-distance: 60;}
'''
    p.write_text(s, encoding="utf-8")
    parking_count += 1
    print("v1.2 parking style:", p.relative_to(ROOT))
if parking_count < 3:
    raise SystemExit(f"unexpected Icons style count: {parking_count}")

print(f"CB6 Navi v1.2 fixes applied to {style_count} label styles and {parking_count} icon styles.")
