#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text(encoding="utf-8")

# Run #69 real-device result: proven traffic signals render, convenience marks do not.
# Keep the signal class/branch byte-for-byte unchanged and route only convenience
# kinds through an explicit DebugMarkPoint-derived renderer in the same proven group.
loop_anchor = "    for (jsize i = 0; i < n; ++i)\n    {\n"
convenience_class = r'''    class Cb6ConvenienceMark final : public DebugMarkPoint
    {
    public:
      Cb6ConvenienceMark(m2::PointD const & pt, int kind) : DebugMarkPoint(pt), m_kind(kind) {}
      drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames() const override
      {
        auto symbols = make_unique_dp<SymbolNameZoomInfo>();
        char const * xs = "cb6-convenience-xs";
        char const * sm = "cb6-convenience-s";
        char const * normal = "cb6-convenience";
        switch (m_kind)
        {
        case 1: xs = "cb6-seven-xs"; sm = "cb6-seven-s"; normal = "cb6-seven"; break;
        case 2: xs = "cb6-familymart-xs"; sm = "cb6-familymart-s"; normal = "cb6-familymart"; break;
        case 3: xs = "cb6-lawson-xs"; sm = "cb6-lawson-s"; normal = "cb6-lawson"; break;
        case 4: xs = "cb6-seicomart-xs"; sm = "cb6-seicomart-s"; normal = "cb6-seicomart"; break;
        case 5: xs = "cb6-mybasket-xs"; sm = "cb6-mybasket-s"; normal = "cb6-mybasket"; break;
        case 8: xs = "cb6-ministop-xs"; sm = "cb6-ministop-s"; normal = "cb6-ministop"; break;
        case 9: xs = "cb6-daily-xs"; sm = "cb6-daily-s"; normal = "cb6-daily"; break;
        default: break;
        }
        symbols->insert({12, xs});
        symbols->insert({14, sm});
        symbols->insert({15, normal});
        return symbols;
      }
      int GetMinZoom() const override { return 12; }
      bool SymbolIsPOI() const override { return true; }
      bool IsNonDisplaceable() const override { return true; }
      bool GetDepthTestEnabled() const override { return false; }

    private:
      int m_kind;
    };

'''
if "class Cb6ConvenienceMark final" not in s:
    # Insert in nativeSetCb6DrivingMarks after the local signal renderer and before its mark loop.
    native_pos = s.find("JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6DrivingMarks")
    if native_pos < 0:
        raise SystemExit("nativeSetCb6DrivingMarks not found")
    loop_pos = s.find(loop_anchor, native_pos)
    if loop_pos < 0:
        raise SystemExit("native mark loop not found")
    s = s[:loop_pos] + convenience_class + s[loop_pos:]

old = '''      auto * mark = session.CreateUserMark<Cb6DrivingMark>(pt);
      mark->SetKind(static_cast<int>(kinds[i]));'''
new = '''      int const kind = static_cast<int>(kinds[i]);
      if ((kind >= 1 && kind <= 6) || kind == 8 || kind == 9)
      {
        session.CreateUserMark<Cb6ConvenienceMark>(pt, kind);
        continue;
      }
      auto * mark = session.CreateUserMark<Cb6DrivingMark>(pt);
      mark->SetKind(kind);'''
if new not in s:
    if old not in s:
        raise SystemExit("generic CB6 mark branch not found")
    s = s.replace(old, new, 1)

required = (
    'class Cb6ConvenienceMark final : public DebugMarkPoint',
    'Cb6ConvenienceMark(m2::PointD const & pt, int kind) : DebugMarkPoint(pt), m_kind(kind) {}',
    'symbols->insert({12, xs});',
    'symbols->insert({14, sm});',
    'symbols->insert({15, normal});',
    'int GetMinZoom() const override { return 12; }',
    'session.CreateUserMark<Cb6ConvenienceMark>(pt, kind);',
    'class Cb6SignalMark final : public DebugMarkPoint',
)
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("convenience renderer requirements missing: " + ", ".join(missing))

fw.write_text(s, encoding="utf-8")
print("CB6 convenience marks routed through explicit proven DebugMarkPoint renderer; signal renderer unchanged")
