#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

def read(rel):
    p = ROOT / rel
    if not p.exists(): raise SystemExit("missing: " + rel)
    return p.read_text(encoding="utf-8")
def write(rel,s):
    p=ROOT/rel; p.write_text(s,encoding="utf-8"); print("v1.1 patched:",rel)
def once(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f"{label}: expected 1 match, got {n}")
    return s.replace(old,new,1)
def once_or_already(s,old,new,label):
    n=s.count(old)
    if n==1: return s.replace(old,new,1)
    if n==0 and new in s:
        print("v1.1 already applied:", label)
        return s
    raise SystemExit(f"{label}: expected 1 match or already-patched target, got {n}")
rel="android/sdk/src/main/java/app/organicmaps/sdk/Framework.java"; s=read(rel); anchor="  public static native String nativeGetAddress(double lat, double lon);\n"; s=once_or_already(s,anchor,anchor+"  public static native String nativeGetStreetName(double lat, double lon);\n","nativeGetStreetName declaration"); write(rel,s)
rel="android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"; s=read(rel); pat=re.compile(r"(JNIEXPORT jstring JNICALL Java_app_organicmaps_sdk_Framework_nativeGetAddress\(.*?\n\{\n  auto const info = frm\(\)->GetAddressAtPoint\(mercator::FromLatLon\(lat, lon\)\);\n  return jni::ToJavaString\(env, info\.FormatAddress\(\)\);\n\}\n)",re.S); m=pat.search(s)
extra='''\nJNIEXPORT jstring JNICALL Java_app_organicmaps_sdk_Framework_nativeGetStreetName(JNIEnv * env, jclass clazz, jdouble lat, jdouble lon)\n{\n  auto const info = frm()->GetAddressAtPoint(mercator::FromLatLon(lat, lon));\n  return jni::ToJavaString(env, info.GetStreetName());\n}\n'''
if "Java_app_organicmaps_sdk_Framework_nativeGetStreetName" not in s:
    if not m: raise SystemExit("nativeGetAddress implementation not found")
    s=s[:m.end()]+extra+s[m.end():]
else: print("v1.1 already applied: nativeGetStreetName implementation")
write(rel,s)
rel="android/app/src/main/java/app/organicmaps/MwmActivity.java"; s=read(rel); s=once_or_already(s,"      updateCb6RoadHud(Framework.nativeGetAddress(location.getLatitude(), location.getLongitude()));","      updateCb6RoadHud(Framework.nativeGetStreetName(location.getLatitude(), location.getLongitude()));","road HUD street lookup"); s=once_or_already(s,"    mCb6SupplementManager = new Cb6SupplementManager(getApplicationContext());\n\n    if (mCb6GoogleMaps != null)","    mCb6SupplementManager = new Cb6SupplementManager(getApplicationContext());\n    applyCb6UiSizing();\n\n    if (mCb6GoogleMaps != null)","CB6 UI sizing call")
method_anchor="  private void updateCb6RoadHud(@Nullable String raw)\n"; helper='''  private int cb6Dp(int dp)\n  {\n    return Math.round(dp * getResources().getDisplayMetrics().density);\n  }\n\n  private void applyCb6UiSizing()\n  {\n    final boolean landscape = getResources().getConfiguration().orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE;\n    if (mCb6RoadHud != null) { android.view.ViewGroup.LayoutParams lp=mCb6RoadHud.getLayoutParams(); lp.width=cb6Dp(landscape ? 170 : 210); lp.height=cb6Dp(32); mCb6RoadHud.setLayoutParams(lp); mCb6RoadHud.setMinWidth(cb6Dp(landscape ? 170 : 210)); mCb6RoadHud.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, landscape ? 13 : 14); if (lp instanceof android.view.ViewGroup.MarginLayoutParams) ((android.view.ViewGroup.MarginLayoutParams)lp).bottomMargin=cb6Dp(landscape ? 50 : 54); }\n    if (mCb6GoogleMaps != null) { android.view.ViewGroup.LayoutParams lp=mCb6GoogleMaps.getLayoutParams(); lp.width=cb6Dp(landscape ? 54 : 60); lp.height=cb6Dp(32); mCb6GoogleMaps.setLayoutParams(lp); mCb6GoogleMaps.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP,11); if (lp instanceof android.view.ViewGroup.MarginLayoutParams) ((android.view.ViewGroup.MarginLayoutParams)lp).bottomMargin=cb6Dp(landscape ? 50 : 54); }\n  }\n\n'''
if helper not in s: s=once(s,method_anchor,helper+method_anchor,"CB6 UI sizing helper")
else: print("v1.1 already applied: CB6 UI sizing helper")
write(rel,s)
rel="libs/map/user_mark.cpp"; s=read(rel); s=once_or_already(s,'symbols->insert({15, "cb6-stop"});','symbols->insert({14, "cb6-stop"});',"stop small zoom"); s=once_or_already(s,'symbols->insert({17, "cb6-stop-l"});','symbols->insert({16, "cb6-stop-l"});',"stop large zoom")
for name in ("seven","familymart","lawson","seicomart","mybasket","ministop","daily","convenience"): s=once_or_already(s,f'{{13, "cb6-{name}"}}',f'{{12, "cb6-{name}"}}',f"{name} zoom")
s=once_or_already(s,'symbols->insert({14, "cb6-signal"});','symbols->insert({13, "cb6-signal"});',"signal small zoom"); s=once_or_already(s,'symbols->insert({17, "cb6-signal-l"});','symbols->insert({16, "cb6-signal-l"});',"signal large zoom")
old_min="    return 14;\n  if (m_kind == 0)\n    return 15;\n  return 13;"
new_min="    return 13;\n  if (m_kind == 0)\n    return 14;\n  return 12;"
if old_min in s: s=s.replace(old_min,new_min,1)
elif new_min in s: print("v1.1 already applied: CB6 min zoom")
else: print("v1.1 compatibility: CB6 min zoom already differs in current source; preserving current implementation")
write(rel,s)
suppress='''\n\n/* CB6 v1.1: suppress fine address/block clutter while retaining road and major-place names. */\nnode|z13-[place=suburb],\nnode|z13-[place=locality],\nnode|z13-[place=quarter],\nnode|z13-[place=neighbourhood],\nnode|z17-[landuse=residential]\n{text:none;}\n'''
for style in ("default","vehicle","driving"):
 p=ROOT/f"data/styles/{style}/include/Basemap_label.mapcss"
 if p.exists():
  s=p.read_text(encoding="utf-8")
  if "CB6 v1.1: suppress fine address/block clutter" not in s: p.write_text(s+suppress,encoding="utf-8")
priority_bases=("place-suburb","place-locality","place-quarter","place-neighbourhood","landuse-residential")
for prio in (ROOT/"data/styles").glob("*/include/priorities_4_overlays.prio.txt"):
 lines=prio.read_text(encoding="utf-8").splitlines(); changed=False
 for base in priority_bases:
  intl=base+"::int_name"
  if any(line.strip().split("#",1)[0].strip()==intl for line in lines): continue
  idx=[i for i,line in enumerate(lines) if line.strip().split("#",1)[0].strip()==base]
  if not idx: continue
  marker=next((j for j in range(idx[0]+1,min(len(lines),idx[0]+40)) if lines[j].strip().startswith("===")),None)
  if marker is None: raise SystemExit(f"priority marker not found for {base} in {prio}")
  lines.insert(marker,f"{intl:<52} # CB6 same priority as {base}"); changed=True
 if changed: prio.write_text("\n".join(lines)+"\n",encoding="utf-8")
signal_rule="node|z14-[highway=traffic_signals]\n{icon-image: traffic_signals.svg;}"
for style in ("default","vehicle","driving"):
 p=ROOT/f"data/styles/{style}/include/Icons.mapcss"
 if not p.exists(): continue
 s=p.read_text(encoding="utf-8").replace("node|z19-[highway=traffic_signals]\n{icon-image: traffic_signals.svg;}",signal_rule)
 if signal_rule not in s: s+='''\n\n/* CB6 v1.1 native traffic-signal fallback for normal map/driving views. */\nnode|z14-[highway=traffic_signals]\n{icon-image: traffic_signals.svg;}\n'''
 p.write_text(s,encoding="utf-8")
prio=ROOT/"data/styles/default/include/priorities_4_overlays.prio.txt"
if prio.exists():
 lines=prio.read_text(encoding="utf-8").splitlines()
 if not any(line.strip().split("#",1)[0].strip()=="highway-traffic_signals" for line in lines): lines.extend(["","highway-traffic_signals                             # CB6 v1.1 icon z14-","=== 215"]); prio.write_text("\n".join(lines)+"\n",encoding="utf-8")
print("CB6 Navi v1.1 real-device fixes applied.")
