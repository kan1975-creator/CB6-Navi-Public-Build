#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve()
P=[]; F=[]
def check(v,m): (P if v else F).append(m)
def txt(rel):
    p=ROOT/rel
    if not p.exists(): F.append('missing '+rel); return ''
    return p.read_text(encoding='utf-8',errors='replace')
fw=txt('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp')
uh=txt('libs/map/user_mark.hpp')
uc=txt('libs/map/user_mark.cpp')
mgr=txt('android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java')
for token in (
    'class Cb6SignalMark final : public DebugMarkPoint',
    'DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING)',
    'session.ClearGroup(UserMark::Type::CB6_DRIVING);',
    'session.SetIsVisible(UserMark::Type::CB6_DRIVING, true);',
    'session.CreateUserMark<Cb6SignalMark>(pt)',
    'IsNonDisplaceable() const override { return true; }',
    'GetDepthTestEnabled() const override { return false; }',
    'session.NotifyChanges();'):
    check(token in fw,'framework '+token)
check('DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type);' in uh,'typed DebugMarkPoint constructor declaration')
check('DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type)' in uc,'typed DebugMarkPoint constructor implementation')
check('CB6_DRIVING' in uh,'CB6_DRIVING type declared')
check('Framework.nativeSetCb6DrivingMarks' in mgr,'Java publishes CB6 marks through JNI')
check('GetMarkType() const override' not in fw,'no invalid non-virtual GetMarkType override')
print(f'V111_CHECKS={len(P)+len(F)} PASS={len(P)} FAIL={len(F)}')
for x in P: print('PASS',x)
for x in F: print('FAIL',x)
if F: raise SystemExit(1)
