#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()


def rw(path: Path, fn):
    s = path.read_text(encoding="utf-8")
    n = fn(s)
    if n != s:
        path.write_text(n, encoding="utf-8")
        print("v1.5 patched:", path.relative_to(ROOT))
    return n


def rewrite_caption_zoom(s: str) -> str:
    lines = s.splitlines(keepends=True)
    out, block = [], []
    targets = ("suburb", "locality", "quarter", "neighbourhood")
    def finish(b):
        if not b: return ""
        text = "".join(b)
        prop = text[text.find("{"):] if "{" in text else ""
        if re.search(r"\btext\s*:\s*(?:name|int_name)\b", prop):
            for place in targets:
                text = re.sub(rf"(node|area)\|z\d+(?:-\d+|-)?(?=\[place={place}\])", r"\1|z17-", text)
            text = re.sub(r"(node|area)\|z\d+(?:-\d+|-)?(?=\[landuse=residential\])", r"\1|z17-", text)
        return text
    for line in lines:
        block.append(line)
        if "{" in line and "}" in line:
            out.append(finish(block)); block = []
    out.append("".join(block))
    return "".join(out)


def strip_native_signal_rules(s: str) -> str:
    lines=s.splitlines(keepends=True); out=[]; block=[]; in_block=False
    for line in lines:
        if not in_block:
            block=[line]
            if "{" in line:
                in_block=True
                if "}" in line:
                    text="".join(block)
                    if "[highway=traffic_signals]" not in text: out.extend(block)
                    block=[]; in_block=False
            elif line.strip().startswith("/*") or line.strip().startswith("//") or not line.strip(): out.append(line)
            else: in_block=True
        else:
            block.append(line)
            if "}" in line:
                text="".join(block)
                if "[highway=traffic_signals]" not in text: out.extend(block)
                block=[]; in_block=False
    if block: out.extend(block)
    return re.sub(r"\n?/\* CB6[^*]*(?:traffic[- ]signal|native signal)[^*]*\*/\n?", "\n", "".join(out), flags=re.I)

label_files=sorted((ROOT/"data/styles").glob("*/include/Basemap_label.mapcss"))
if len(label_files)<3: raise SystemExit(f"unexpected label style count: {len(label_files)}")
for p in label_files: rw(p,rewrite_caption_zoom)

activity=ROOT/"android/app/src/main/java/app/organicmaps/MwmActivity.java"
s=activity.read_text(encoding="utf-8")
reapply_block='''    refreshCb6FromSavedLocation();\n    if (mCb6SupplementManager != null)\n    {\n      final android.view.View cb6Decor = getWindow().getDecorView();\n      cb6Decor.postDelayed(() -> {\n        if (mCb6SupplementManager != null)\n          mCb6SupplementManager.reapplySavedMarks();\n      }, 1800L);\n      cb6Decor.postDelayed(() -> {\n        if (mCb6SupplementManager != null)\n          mCb6SupplementManager.reapplySavedMarks();\n      }, 5000L);\n    }\n'''
if "mCb6SupplementManager.reapplySavedMarks();" not in s:
    restart_anchor="    ThemeSwitcher.INSTANCE.restart(true);\n"
    if restart_anchor not in s: raise SystemExit("ThemeSwitcher restart anchor missing")
    s=s.replace(restart_anchor,restart_anchor+reapply_block,1)
old_loc='''    if (mCb6SupplementManager != null)\n      mCb6SupplementManager.onLocation(location);\n\n    final RoutingController routing = RoutingController.get();\n    if (!routing.isNavigating())\n    {\n      updateCb6RoadHud(Framework.nativeGetStreetName(location.getLatitude(), location.getLongitude()));\n      return;\n    }\n'''
new_loc='''    updateCb6FromLocation(location);\n\n    final RoutingController routing = RoutingController.get();\n    if (!routing.isNavigating())\n      return;\n'''
if old_loc in s: s=s.replace(old_loc,new_loc,1)
helper_anchor="  private void updateCb6RoadHud(@Nullable String raw)\n"
helper='''  private void refreshCb6FromSavedLocation()\n  {\n    final Location location = MwmApplication.from(this).getLocationHelper().getSavedLocation();\n    if (location != null)\n      updateCb6FromLocation(location);\n  }\n\n  private void updateCb6FromLocation(@NonNull Location location)\n  {\n    if (mCb6SupplementManager != null)\n      mCb6SupplementManager.onLocation(location);\n\n    String road = Framework.nativeGetStreetName(location.getLatitude(), location.getLongitude());\n    if (road == null || road.trim().isEmpty())\n      road = Framework.nativeGetAddress(location.getLatitude(), location.getLongitude());\n    updateCb6RoadHud(road);\n  }\n\n'''
if "private void refreshCb6FromSavedLocation()" not in s:
    if helper_anchor not in s: raise SystemExit("road HUD helper anchor missing")
    s=s.replace(helper_anchor,helper+helper_anchor,1)
activity.write_text(s,encoding="utf-8"); print("v1.5 patched:",activity.relative_to(ROOT))

manager=ROOT/"android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
ms=manager.read_text(encoding="utf-8")
required_manager=("MAX_POINTS = 2200","KIND_SIGNAL_FULL = 7","KIND_SIGNAL_CLUSTER = 20","public void reapplySavedMarks()","[shop=convenience]","[highway=traffic_signals]","[highway=stop]","out center tags")
missing=[x for x in required_manager if x not in ms]
if missing: raise SystemExit("CB6 supplement source missing: "+", ".join(missing))
# Earlier patch stages may rewrite the exact retry-delay expression. Verify the
# behavior structurally instead of requiring one historical whitespace/expression form.
retry_policy=("mLastRequestTime" in ms and "REFRESH_MS" in ms and "applySavedCache();" in ms and "取得失敗" in ms)
if not retry_policy: raise SystemExit("CB6 supplement retry/cache policy missing")
legacy_cluster="SIGNAL_CLUSTER_M = 55.0f" in ms and "clusterSignals(signals, SIGNAL_CLUSTER_M)" in ms
old_diagnostic="MAX_SIGNAL_POINTS = 1400" in ms and "SIG TEST: JNIへ1件送信" in ms
persistent_diagnostic=("MAX_SIGNAL_POINTS = 1400" in ms and "mDiagnosticLat" in ms and "mDiagnosticLon" in ms and "postDiagnosticOnly()" in ms and "+ 0.00108" in ms and "merged.add(mDiagnosticLat, mDiagnosticLon, KIND_SIGNAL_FULL);" in ms)
if not (legacy_cluster or old_diagnostic or persistent_diagnostic): raise SystemExit("CB6 supplement signal policy missing: neither legacy cluster nor diagnostic signal path found")
for forbidden in ("[amenity=fuel]","[amenity=hospital]","[railway=station]","[shop=supermarket]","[shop=mall]","[aeroway=aerodrome]"):
    if forbidden in ms: raise SystemExit("standard CoMaps POI must not be supplemented: "+forbidden)

u=ROOT/"libs/map/user_mark.cpp"; us=u.read_text(encoding="utf-8")
for name in ("seven","familymart","lawson","seicomart","mybasket","ministop","daily","convenience"):
    us=re.sub(rf'\{{\d+, "cb6-{name}"\}}',f'{{11, "cb6-{name}"}}',us)
signal_case=re.compile(r'''  case 7:\n(?:    symbols->insert\(\{\d+, "cb6-signal(?:-m|-l)?"\}\);\n)+    break;(?:\n  case 20:\n(?:    symbols->insert\(\{\d+, "cb6-signal(?:-m|-l)?"\}\);\n)+    break;)?''')
signal_replacement='''  case 7:\n    symbols->insert({10, "cb6-signal-m"});\n    symbols->insert({14, "cb6-signal-l"});\n    break;\n  case 20:\n    symbols->insert({9, "cb6-signal"});\n    symbols->insert({10, "cb6-signal-m"});\n    symbols->insert({14, "cb6-signal-l"});\n    break;'''
us,signal_n=signal_case.subn(signal_replacement,us,count=1)
if signal_n!=1: raise SystemExit("signal split-layer replacement failed")
us=re.sub(r'\{\d+, "cb6-stop"\}','{13, "cb6-stop"}',us); us=re.sub(r'\{\d+, "cb6-stop-l"\}','{16, "cb6-stop-l"}',us)
us,n=re.subn(r'int Cb6DrivingMark::GetMinZoom\(\) const\n\{.*?\n\}','''int Cb6DrivingMark::GetMinZoom() const\n{\n  if (m_kind == 7)\n    return 10;\n  if (m_kind == 20)\n    return 9;\n  if (m_kind == 0)\n    return 13;\n  return 11;\n}''',us,count=1,flags=re.S)
if n!=1: raise SystemExit("GetMinZoom replacement failed")
for forbidden in ("cb6-fuel","cb6-hospital","cb6-station","cb6-supermarket","cb6-mall","cb6-airport"):
    if forbidden in us: raise SystemExit("standard landmark leaked into CB6 UserMarks: "+forbidden)
u.write_text(us,encoding="utf-8"); print("v1.5 patched:",u.relative_to(ROOT))

for p in sorted((ROOT/"data/styles").glob("*/include/Icons.mapcss")):
    before=p.read_text(encoding="utf-8"); after=strip_native_signal_rules(before)
    if after!=before: p.write_text(after,encoding="utf-8"); print("v1.5 native signal rendering removed:",p.relative_to(ROOT))

low_zoom_rules={"default":'''\n\n/* CB6 v1.5: native major-landmark low-zoom bridge; no Overpass duplication. */\nnode|z12-13[amenity=fuel]\n{icon-image: fuel-s.svg; icon-min-distance: 24;}\nnode|z13-14[amenity=hospital]\n{icon-image: hospital-m.svg; icon-min-distance: 22;}\nnode|z13-15[shop=supermarket]\n{icon-image: supermarket-m.svg; icon-min-distance: 22;}\nnode|z12-13[shop=mall]\n{icon-image: shop-s.svg; icon-min-distance: 24;}\n''',"vehicle":'''\n\n/* CB6 v1.5: native major-landmark low-zoom bridge; no Overpass duplication. */\nnode|z13-14[amenity=hospital]\n{icon-image: hospital-m.svg; icon-min-distance: 20;}\nnode|z12-13[shop=supermarket]\n{icon-image: supermarket-m.svg; icon-min-distance: 20;}\nnode|z12-13[shop=mall]\n{icon-image: shop-m.svg; icon-min-distance: 20;}\n'''}
for style,block in low_zoom_rules.items():
    p=ROOT/"data/styles"/style/"include"/"Icons.mapcss"
    if not p.exists(): raise SystemExit("missing native landmark style: "+str(p.relative_to(ROOT)))
    text=p.read_text(encoding="utf-8")
    if "CB6 v1.5: native major-landmark low-zoom bridge" not in text: p.write_text(text+block,encoding="utf-8"); print("v1.5 native landmarks:",p.relative_to(ROOT))
print(f"CB6 Navi v1.5 FinalRenderFix applied to {len(label_files)} label styles; native signal icons disabled; legacy signal stage retained for regression, with v1.6 authoritative override applied later.")