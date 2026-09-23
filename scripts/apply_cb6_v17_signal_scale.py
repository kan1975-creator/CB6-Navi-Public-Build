#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text(encoding="utf-8")

# v1.8 intentionally replaces the v1.7 zoom policy while preserving the same
# Run #138 DebugMarkPoint renderer. CB6_V16_AUDIT runs both before and after
# generated-resource creation, so treat an already-applied v1.8 class as a valid
# idempotent state instead of trying to rewrite it back to v1.7.
if 'void SetForward(bool forward)' in s:
    required_v18 = (
        'class Cb6SignalMark final : public DebugMarkPoint',
        'symbols->insert({15, "cb6-signal"});',
        'symbols->insert({17, "cb6-signal-m"});',
        'symbols->insert({19, "cb6-signal-l"});',
        'int GetMinZoom() const override { return 15; }',
        'auto * mark = session.CreateUserMark<Cb6SignalMark>(pt);',
        'mark->SetForward(static_cast<int>(kinds[i]) == 22);',
    )
    for token in required_v18:
        if token not in s:
            raise SystemExit("v1.8 signal policy incomplete: " + token)
    print("CB6 signal scale: v1.8 forward policy already applied; v1.7 patch skipped")
    raise SystemExit(0)

old = '''      drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames() const override
      {
        auto symbols = make_unique_dp<SymbolNameZoomInfo>();
        symbols->insert({1, "cb6-signal-l"});
        return symbols;
      }'''
new = '''      drape_ptr<df::UserPointMark::SymbolNameZoomInfo> GetSymbolNames() const override
      {
        auto symbols = make_unique_dp<SymbolNameZoomInfo>();
        // CB6 v1.7 compatibility policy. v1.8 supersedes this after the baseline
        // renderer is established.
        symbols->insert({1, "cb6-signal-s"});
        symbols->insert({15, "cb6-signal"});
        symbols->insert({17, "cb6-signal-m"});
        symbols->insert({19, "cb6-signal-l"});
        return symbols;
      }'''
if old not in s:
    if new not in s:
        raise SystemExit("Cb6SignalMark symbol policy replacement point not found")
else:
    s = s.replace(old, new, 1)

# Preserve the exact Run #138 proven-visible class path. Do not add back any
# extra render-policy overrides here.
for forbidden in (
    'bool SymbolIsPOI() const override { return true; }',
    'bool IsNonDisplaceable() const override { return true; }',
    'bool GetDepthTestEnabled() const override { return false; }',
):
    start = s.find('class Cb6SignalMark final : public DebugMarkPoint')
    end = s.find('    };', start)
    if start >= 0 and end >= 0 and forbidden in s[start:end]:
        raise SystemExit("unexpected extra Cb6SignalMark render override: " + forbidden)

required = (
    'symbols->insert({1, "cb6-signal-s"});',
    'symbols->insert({15, "cb6-signal"});',
    'symbols->insert({17, "cb6-signal-m"});',
    'symbols->insert({19, "cb6-signal-l"});',
    'int GetMinZoom() const override { return 1; }',
)
for token in required:
    if token not in s:
        raise SystemExit("scaled signal policy missing: " + token)

fw.write_text(s, encoding="utf-8")
print("CB6 signal scale applied: z1 small, z15 normal, z17 medium, z19 large")
