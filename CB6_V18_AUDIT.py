#!/usr/bin/env python3
from pathlib import Path
import sys

R = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
fw = (R / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp").read_text(encoding="utf-8")
mgr = (R / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java").read_text(encoding="utf-8")

def ck(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        raise SystemExit(1)

ck("Run138 DebugMarkPoint path preserved", "class Cb6SignalMark final : public DebugMarkPoint" in fw)
ck("500m class visible via z14 minimum", "int GetMinZoom() const override { return 14; }" in fw)
ck("500m half-size signal at z14 and normal size restored at z15", 'symbols->insert({14, "cb6-signal-500"});' in fw and 'symbols->insert({15, "cb6-signal"});' in fw)
ck("forward-only medium at z17", 'if (m_forward)' in fw and 'symbols->insert({17, "cb6-signal-m"});' in fw)
ck("forward-only large at z19", 'if (m_forward)' in fw and 'symbols->insert({19, "cb6-signal-l"});' in fw)
ck("forward kind creates forward signal mark", 'static_cast<int>(kinds[i]) == 22' in fw and 'auto * mark = session.CreateUserMark<Cb6SignalMark>(pt);' in fw and 'mark->SetForward(static_cast<int>(kinds[i]) == 22);' in fw)
ck("native MapCSS signal selector still absent", all("[highway=traffic_signals]" not in p.read_text(encoding="utf-8") for p in (R / "data/styles").glob("*/include/Icons.mapcss")))
ck("manager forward kind present", "KIND_SIGNAL_FORWARD = 22" in mgr)
ck("manager keeps current bearing", "location.hasBearing()" in mgr and "mCurrentBearing = location.getBearing();" in mgr)
ck("manager forward cone limited", "FORWARD_SIGNAL_MAX_M = 450.0f" in mgr and "FORWARD_CONE_DEG = 45.0f" in mgr)
ck("manager sends directional kinds", "kindsForCurrentDirection(points)" in mgr)
ck("nearby signals prioritized before cap", "parseSignalsNearFirst" in mgr and "signals.sort((a, b) -> Double.compare(a[2], b[2]))" in mgr)
ck("Overpass signal acquisition preserved", "[highway=traffic_signals]" in mgr)
ck("cache path preserved", "applySavedCache();" in mgr)
print("CB6 v1.8 forward-signal 500m audit passed")
