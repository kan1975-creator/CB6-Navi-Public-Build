#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

# Keep the renderer behavior that was proven on-device with DebugMarkPoint, but
# construct signal marks with the CB6_DRIVING mark type. UserMark::GetMarkType()
# is intentionally non-virtual in pinned CoMaps, so overriding GetMarkType() in
# Cb6SignalMark is invalid C++ and would not change the group anyway. Add a small
# typed DebugMarkPoint constructor instead; all rendering virtuals remain those
# of DebugMarkPoint/Cb6SignalMark while the underlying mark id belongs to
# CB6_DRIVING.

hpp = ROOT / "libs/map/user_mark.hpp"
h = hpp.read_text(encoding="utf-8")
old_decl = '''class DebugMarkPoint : public UserMark
{
public:
  explicit DebugMarkPoint(m2::PointD const & ptOrg);

  drape_ptr<SymbolNameZoomInfo> GetSymbolNames() const override;
};'''
new_decl = '''class DebugMarkPoint : public UserMark
{
public:
  explicit DebugMarkPoint(m2::PointD const & ptOrg);
  DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type);

  drape_ptr<SymbolNameZoomInfo> GetSymbolNames() const override;
};'''
if old_decl in h:
    h = h.replace(old_decl, new_decl, 1)
elif 'DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type);' not in h:
    raise SystemExit("v1.11 typed DebugMarkPoint declaration anchor not found")
hpp.write_text(h, encoding="utf-8")

cpp = ROOT / "libs/map/user_mark.cpp"
c = cpp.read_text(encoding="utf-8")
old_impl = 'DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg) : UserMark(ptOrg, UserMark::Type::DEBUG_MARK) {}'
new_impl = '''DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg) : UserMark(ptOrg, UserMark::Type::DEBUG_MARK) {}

DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type) : UserMark(ptOrg, type) {}'''
if old_impl in c and 'DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type)' not in c:
    c = c.replace(old_impl, new_impl, 1)
elif 'DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type)' not in c:
    raise SystemExit("v1.11 typed DebugMarkPoint implementation anchor not found")
cpp.write_text(c, encoding="utf-8")

fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text(encoding="utf-8")
old_ctor = 'explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt) {}'
new_ctor = 'explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING) {}'
if old_ctor in s:
    s = s.replace(old_ctor, new_ctor, 1)
elif new_ctor not in s:
    raise SystemExit("v1.11 signal constructor anchor not found")

# Remove the invalid/non-functional override if an earlier interrupted patch left it.
s = s.replace('\n      UserMark::Type GetMarkType() const override { return UserMark::Type::CB6_DRIVING; }', '', 1)

old_group = '''    session.ClearGroup(UserMark::Type::DEBUG_MARK);
    session.SetIsVisible(UserMark::Type::DEBUG_MARK, true);'''
new_group = '''    session.ClearGroup(UserMark::Type::DEBUG_MARK);
    session.SetIsVisible(UserMark::Type::DEBUG_MARK, true);
    session.ClearGroup(UserMark::Type::CB6_DRIVING);
    session.SetIsVisible(UserMark::Type::CB6_DRIVING, true);'''
if old_group in s:
    s = s.replace(old_group, new_group, 1)
elif 'session.SetIsVisible(UserMark::Type::CB6_DRIVING, true);' not in s:
    raise SystemExit("v1.11 group visibility anchor not found")

required = (
    'class Cb6SignalMark final : public DebugMarkPoint',
    'DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING)',
    'session.ClearGroup(UserMark::Type::CB6_DRIVING);',
    'session.SetIsVisible(UserMark::Type::CB6_DRIVING, true);',
    'symbols->insert({15, "cb6-signal"});',
    'IsNonDisplaceable() const override { return true; }',
    'session.CreateUserMark<Cb6SignalMark>(pt)',
    'session.NotifyChanges();',
)
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("v1.11 required signal behavior missing: " + ", ".join(missing))
if 'GetMarkType() const override' in s:
    raise SystemExit("v1.11 invalid GetMarkType override remains")

fw.write_text(s, encoding="utf-8")
print("CB6 v1.11 applied: proven DebugMark renderer retained with real CB6_DRIVING mark type and dedicated visible group")
