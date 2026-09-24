#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('comaps').resolve()

def suppress_buildings(root):
    count = 0
    for p in sorted((root/'data/styles').glob('*/include/Basemap.mapcss')):
        body = p.read_text(encoding='utf-8')
        marker = '/* CB6 runtime-final building geometry hidden */'
        if marker not in body:
            body += '\n' + marker + '\narea|z1-[building],\narea|z1-[building:part]\n{fill-opacity:0; line-width:0;}\n'
            p.write_text(body, encoding='utf-8')
            count += 1
    for p in sorted((root/'data/styles').glob('*/include/Basemap_label.mapcss')):
        body = p.read_text(encoding='utf-8')
        marker = '/* CB6 runtime-final building labels hidden */'
        if marker not in body:
            body += '\n' + marker + '\narea|z1-[building]\n{text:none;}\n'
            p.write_text(body, encoding='utf-8')
            count += 1
    return count

removed_total = suppress_buildings(ROOT)

fw=ROOT/'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp';s=fw.read_text(encoding='utf-8')
required=('class Cb6SignalMark final : public DebugMarkPoint','DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING)','session.SetIsVisible(UserMark::Type::CB6_DRIVING, true);','bool SymbolIsPOI() const override { return true; }','bool IsNonDisplaceable() const override { return true; }','bool GetDepthTestEnabled() const override { return false; }','void SetForward(bool forward)','int GetMinZoom() const override { return 14; }')
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
