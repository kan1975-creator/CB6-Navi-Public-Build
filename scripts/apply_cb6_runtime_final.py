#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('comaps').resolve()

def strip_building_rules(text: str):
    lines=text.splitlines(keepends=True); out=[]; block=[]; depth=0; removed=0
    for line in lines:
        block.append(line)
        depth += line.count('{') - line.count('}')
        if depth == 0 and '}' in line:
            b=''.join(block); selector, body = b.split('{', 1)
            parts = selector.split(',')
            kept = [part for part in parts if not re.search(r'\[(?:building|building:part)(?:[=\]])', part)]
            removed += len(parts) - len(kept)
            if kept:
                out.append(','.join(kept) + '{' + body)
            block=[]
    if block: out.append(''.join(block))
    return ''.join(out), removed

removed_total=0
for p in sorted((ROOT/'data/styles').glob('*/include/*.mapcss')):
    before=p.read_text(encoding='utf-8'); after,n=strip_building_rules(before)
    removed_total += n
    if after != before: p.write_text(after,encoding='utf-8')
# Buildings are intentionally not rendered, but retain an explicit text:none rule so
# house numbers cannot leak back as labels and the final audit can distinguish
# suppression from building geometry rendering.
for p in sorted((ROOT/'data/styles').glob('*/include/Basemap_label.mapcss')):
    s=p.read_text(encoding='utf-8')
    marker='CB6 runtime-final: buildings hidden; suppress building house numbers'
    if marker not in s:
        s += '\n\n/* '+marker+' */\nnode|z10-[building][addr:housenumber]\n{text:none;}\n'
        p.write_text(s,encoding='utf-8')

fw=ROOT/'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp';s=fw.read_text(encoding='utf-8')
required=('class Cb6SignalMark final : public DebugMarkPoint','DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING)','session.SetIsVisible(UserMark::Type::CB6_DRIVING, true);','bool SymbolIsPOI() const override { return true; }','bool IsNonDisplaceable() const override { return true; }','bool GetDepthTestEnabled() const override { return false; }','void SetForward(bool forward)','int GetMinZoom() const override { return 15; }')
miss=[x for x in required if x not in s]
if miss: raise SystemExit('runtime-final: dedicated signal renderer missing: '+', '.join(miss))
if 'GetMarkType() const override' in s: raise SystemExit('runtime-final: invalid non-virtual GetMarkType override detected')
fw.write_text(s,encoding='utf-8')
hpp=ROOT/'libs/map/user_mark.hpp';h=hpp.read_text(encoding='utf-8')
if 'DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type);' not in h: raise SystemExit('runtime-final: typed DebugMarkPoint declaration missing')
cpp=ROOT/'libs/map/user_mark.cpp';c=cpp.read_text(encoding='utf-8')
if 'DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type) : UserMark(ptOrg, type) {}' not in c: raise SystemExit('runtime-final: typed DebugMarkPoint implementation missing')

mgr=ROOT/'android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java';m=mgr.read_text(encoding='utf-8')
need=('postImmediateSignals(signals);','private void postImmediateSignals(@NonNull Points signals)','requestNearbySignalsIfNeeded(lat, lon, now);','postNearbySignals(nearby, lat, lon);','NEAR_SIGNAL_RADIUS_M = 2000','KIND_SIGNAL_FORWARD = 22','FORWARD_SIGNAL_MAX_M = 450.0f','FORWARD_CONE_DEG = 45.0f','parseSignalsNearFirst','MAX_SIGNAL_POINTS = 1400','mLastPublishedPoints = merged.copy();')
miss=[x for x in need if x not in m]
if miss: raise SystemExit('runtime-final: signal acquisition/preservation path incomplete: '+', '.join(miss))
if 'postPoints(signals, "NET-SIG");' in m: raise SystemExit('runtime-final: unsafe signal-only whole-group publisher detected')
old='''        if (nearby.signalCount() == 0)\n        {\n          Log.i(TAG, "near signal refresh returned zero signals; preserving current marks");\n          return;\n        }''';new='''        if (nearby.signalCount() == 0)\n        {\n          Log.i(TAG, "near signal endpoint returned zero; trying next endpoint while preserving marks");\n          continue;\n        }'''
if old in m:m=m.replace(old,new,1)
elif 'near signal endpoint returned zero; trying next endpoint' not in m:raise SystemExit('runtime-final: near-zero fallback anchor missing')
mgr.write_text(m,encoding='utf-8')
for p in sorted((ROOT/'data/styles').glob('*/include/Icons.mapcss')):
    if '[highway=traffic_signals]' in p.read_text(encoding='utf-8'): raise SystemExit('runtime-final: native signal rule reappeared: '+str(p))
print(f'CB6 runtime-final applied: building draw rules removed={removed_total}; house-number suppression retained; signal runtime hardened')
