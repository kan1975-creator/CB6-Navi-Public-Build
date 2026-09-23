#!/usr/bin/env python3
from pathlib import Path
import sys, xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
P, F = [], []

def check(v, msg):
    (P if v else F).append(msg)

def txt(rel):
    p = ROOT / rel
    if not p.exists():
        F.append("missing: " + rel)
        return ""
    return p.read_text(encoding="utf-8", errors="replace")

g = txt("android/app/build.gradle")
check("project.ext.appId = 'jp.cb6.navi'" in g, "independent applicationId")
check("project.ext.appName = 'CB6 Navi'" in g, "CB6 app name")

mwm = txt("android/app/src/main/java/app/organicmaps/MwmActivity.java")
check("Locale.JAPAN" not in mwm, "no Locale.JAPAN force")
check("forceCb6JapaneseLocale" not in mwm, "no legacy locale helper")

for rel in (
    "libs/drape_frontend/my_position.cpp",
    "data/styles/default/light/symbols/current-position.svg",
    "data/styles/default/dark/symbols/current-position.svg",
):
    t = txt(rel)
    check("CB6" not in t and "cb6" not in t, "stock own-position untouched: " + rel)

mapping = txt("data/mapcss-mapping.csv")
check(mapping.count("highway|traffic_signals") == 1, "single native traffic_signals mapping")
check("highway|stop;" not in mapping, "stop not injected into MWM mapping")

styles = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                   for p in ROOT.glob("data/styles/**/*.mapcss"))
check("[entrance][addr:housenumber]" not in styles, "unsafe entrance selector absent")
check("[building][addr:housenumber]" in styles, "building number suppression")
check("place=quarter" in styles and "place=neighbourhood" in styles, "fine locality suppression")

mgr = txt("android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java").lower()
for token in (
    "highway=traffic_signals", "highway=stop", "shop=convenience",
    "7eleven", "familymart", "lawson", "seicomart", "mybasket",
    "ministop", "dailyyamazaki", "overpass-api.de", "overpass.kumi.systems",
):
    check(token in mgr, "supplement manager: " + token)

check("amenity=fuel" not in mgr, "fuel not duplicated")
check("amenity=hospital" not in mgr, "hospital not duplicated")
check("shop=supermarket" not in mgr, "supermarket not duplicated")

fwjava = txt("android/sdk/src/main/java/app/organicmaps/sdk/Framework.java")
fwcpp = txt("android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp")
check("nativeSetCb6DrivingMarks" in fwjava, "Java JNI declaration")
check("Java_app_organicmaps_sdk_Framework_nativeSetCb6DrivingMarks" in fwcpp, "C++ JNI implementation")
check("session.ClearGroup(UserMark::Type::CB6_DRIVING)" in fwcpp, "isolated CB6 mark group clear")
check("CreateUserMark<Cb6DrivingMark>" in fwcpp, "CB6 user marks")

umh = txt("libs/map/user_mark.hpp")
umc = txt("libs/map/user_mark.cpp")
check("CB6_DRIVING" in umh and "CB6_DRIVING" in umc, "CB6 mark type")
check("USER_MARK_TYPES_COUNT_MAX = 1000" in umh, "bookmark category boundary preserved")
check("cb6-signal-l" in umc, "signal near-zoom enlargement")
check("cb6-stop-l" in umc, "stop near-zoom enlargement")

vehicle_icons = txt("data/styles/vehicle/include/Icons.mapcss")
for token in ("shop=convenience", "amenity=fuel", "shop=supermarket", "highway=speed_camera"):
    check(token in vehicle_icons, "stock vehicle POI retained: " + token)
# Legacy builds kept a native traffic-signal fallback. Ver.1.5 intentionally removes
# native signal icon rules so the CB6 UserMark zoom policy is visible on the real device.
# Latest real-device calibration for the 100m disappearance moved the clustered
# representative layer to z9 and the full-node layer to z10, while preserving the
# approved large signal icon from z14.
native_signal_rule = "[highway=traffic_signals]" in vehicle_icons
cb6_only_signal = ("case 20:" in umc and '{9, "cb6-signal"}' in umc and
                   'if (m_kind == 20)\n    return 9;' in umc and
                   '{10, "cb6-signal-m"}' in umc and
                   'if (m_kind == 7)\n    return 10;' in umc and
                   '{14, "cb6-signal-l"}' in umc)
check(native_signal_rule or cb6_only_signal, "traffic signal rendering path")

for token in ("cb6_road_hud", "cb6_google_maps", "CB6_POSITION_LOWER_DP",
              "mCb6SupplementManager.onLocation", "info.currentStreet"):
    check(token in mwm, "MwmActivity: " + token)
check("updateMyPositionRoutingOffset(Math.max(0, offsetY - cb6LowerPx))" in mwm,
      "lower navigation position")

layout = txt("android/app/src/main/res/layout/activity_map.xml")
check('android:id="@+id/cb6_road_hud"' in layout, "road HUD view")
check('android:id="@+id/cb6_google_maps"' in layout, "Google helper view")
try:
    ET.parse(ROOT / "android/app/src/main/res/layout/activity_map.xml")
    P.append("activity_map.xml well formed")
except Exception as e:
    F.append("activity_map.xml parse: " + str(e))

needed = [
 "cb6-stop.svg","cb6-stop-l.svg","cb6-signal.svg","cb6-signal-l.svg",
 "cb6-seven.svg","cb6-familymart.svg","cb6-lawson.svg","cb6-seicomart.svg",
 "cb6-mybasket.svg","cb6-ministop.svg","cb6-daily.svg","cb6-convenience.svg"
]
for theme in ("light","dark"):
    for name in needed:
        p = ROOT / "data/styles/default" / theme / "symbols" / name
        if not p.exists():
            F.append("missing icon: " + theme + "/" + name)
            continue
        try:
            ET.parse(p)
            P.append("SVG " + theme + "/" + name)
        except Exception as e:
            F.append("SVG parse " + theme + "/" + name + ": " + str(e))

check("nativeHasSavedRoutePoints" in fwjava, "saved route API retained")
check("nativeLoadRoutePoints" in fwjava, "route restore API retained")
check("nativeSetAutoReroute" in fwjava, "auto-reroute API retained")

print(f"CHECKS={len(P)+len(F)} PASS={len(P)} FAIL={len(F)}")
for x in P:
    print("PASS", x)
for x in F:
    print("FAIL", x)
if F:
    raise SystemExit(1)
