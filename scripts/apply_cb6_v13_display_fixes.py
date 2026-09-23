#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

def read(rel):
    p = ROOT / rel
    if not p.exists(): raise SystemExit("missing: " + rel)
    return p.read_text(encoding="utf-8")

def write(rel, s):
    p = ROOT / rel
    p.write_text(s, encoding="utf-8")
    print("v1.3 patched:", rel)

def once(s, old, new, label):
    n=s.count(old)
    if n == 1:
        return s.replace(old,new,1)
    if n == 0 and new in s:
        print(f"v1.3 compatibility: {label} already applied")
        return s
    if n == 0:
        print(f"v1.3 compatibility: {label} anchor differs in pinned CoMaps; preserving current implementation")
        return s
    raise SystemExit(f"{label}: expected at most 1 match, got {n}")

for p in sorted((ROOT / "data/styles").glob("*/include/Basemap_label.mapcss")):
    s=p.read_text(encoding="utf-8")
    s=s.replace("node|z10-[place=suburb],", "node|z10-16[place=suburb],")
    s=s.replace("area|z10-[place=suburb],", "area|z10-16[place=suburb],")
    s=s.replace("node|z12-[place=locality],", "node|z12-16[place=locality],")
    s=s.replace("area|z12-[place=locality],", "area|z12-16[place=locality],")
    s=s.replace("node|z12-[place=quarter],", "node|z12-16[place=quarter],")
    s=s.replace("area|z12-[place=quarter],", "area|z12-16[place=quarter],")
    s=s.replace("node|z12-[place=neighbourhood],", "node|z12-16[place=neighbourhood],")
    s=s.replace("area|z12-[place=neighbourhood]", "area|z12-16[place=neighbourhood]")
    s=s.replace("node|z13-[place=suburb],", "node|z13-16[place=suburb],")
    s=s.replace("node|z13-[place=locality],", "node|z13-16[place=locality],")
    s=s.replace("node|z13-[place=quarter],", "node|z13-16[place=quarter],")
    s=s.replace("node|z13-[place=neighbourhood],", "node|z13-16[place=neighbourhood],")
    p.write_text(s,encoding="utf-8")

rel="libs/map/user_mark.cpp"
s=read(rel)
for name in ("seven","familymart","lawson","seicomart","mybasket","ministop","daily","convenience"):
    s=s.replace(f'{{12, "cb6-{name}"}}', f'{{11, "cb6-{name}"}}')
s=s.replace('symbols->insert({13, "cb6-signal"});','symbols->insert({11, "cb6-signal"});')
s=s.replace("    return 13;\n  if (m_kind == 0)\n    return 14;\n  return 12;", "    return 11;\n  if (m_kind == 0)\n    return 14;\n  return 11;")
write(rel,s)

for p in sorted((ROOT / "data/styles").glob("*/include/Icons.mapcss")):
    s=p.read_text(encoding="utf-8")
    s=s.replace("node|z14-[highway=traffic_signals]", "node|z12-[highway=traffic_signals]")
    p.write_text(s,encoding="utf-8")

rel="android/app/src/main/java/app/organicmaps/MwmActivity.java"
s=read(rel)
s=once(s,'''      lp.width = cb6Dp(landscape ? 170 : 210);\n      lp.height = cb6Dp(32);''','''      lp.width = cb6Dp(landscape ? 150 : 190);\n      lp.height = cb6Dp(28);''',"road HUD compact size")
s=s.replace("mCb6RoadHud.setMinWidth(cb6Dp(landscape ? 170 : 210));","mCb6RoadHud.setMinWidth(cb6Dp(landscape ? 150 : 190));")
s=s.replace("mCb6RoadHud.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, landscape ? 13 : 14);","mCb6RoadHud.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, landscape ? 12 : 13);")
s=s.replace("((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 50 : 54);","((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 46 : 50);",1)
s=once(s,'''      lp.width = cb6Dp(landscape ? 54 : 60);\n      lp.height = cb6Dp(32);''','''      lp.width = cb6Dp(landscape ? 48 : 52);\n      lp.height = cb6Dp(28);''',"Google compact size")
s=s.replace("mCb6GoogleMaps.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 11);","mCb6GoogleMaps.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 10);")
needle="((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 50 : 54);"
if needle in s:
    s=s.replace(needle,"((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 92 : 100);",1)
elif "((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 92 : 100);" in s:
    print("v1.3 compatibility: Google bottom margin already applied")
else:
    print("v1.3 compatibility: Google bottom margin anchor differs in pinned CoMaps; preserving current implementation")
write(rel,s)
print("CB6 Navi v1.3 display fixes applied.")
