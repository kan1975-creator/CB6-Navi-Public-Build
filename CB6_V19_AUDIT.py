#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
ms = mgr.read_text(encoding="utf-8")
fs = fw.read_text(encoding="utf-8")

errors = []

def need(text, token, label):
    if token not in text:
        errors.append("missing " + label + ": " + token)

need(ms, 'postImmediateSignals(signals);', "immediate signal publish")
need(ms, 'String poiQuery = buildPoiQuery(lat, lon);', "optional POI request")
if 'postImmediateSignals(signals);' in ms and 'String poiQuery = buildPoiQuery(lat, lon);' in ms:
    if ms.index('postImmediateSignals(signals);') > ms.index('String poiQuery = buildPoiQuery(lat, lon);'):
        errors.append("immediate signal publish occurs after POI enrichment starts")
if ms.count('postImmediateSignals(signals);') != 1:
    errors.append("immediate signal publish count is not exactly one")

# Preserve validated v1.8 manager policy.
for token, label in (
    ('KIND_SIGNAL_FORWARD = 22', 'kind 22'),
    ('FORWARD_SIGNAL_MAX_M = 450.0f', '450m forward limit'),
    ('FORWARD_CONE_DEG = 45.0f', '45 degree cone'),
    ('parseSignalsNearFirst', 'near-first retention'),
    ('MAX_SIGNAL_POINTS = 1400', 'signal cap'),
    ('kindsForCurrentDirection(points)', 'direction mapping'),
):
    need(ms, token, label)

# Preserve validated renderer path/properties.
for token, label in (
    ('class Cb6SignalMark final : public DebugMarkPoint', 'DebugMarkPoint signal path'),
    ('GetMinZoom() const override { return 15; }', 'z15 minimum'),
    ('symbols->insert({17, "cb6-signal-m"});', 'z17 forward icon'),
    ('symbols->insert({19, "cb6-signal-l"});', 'z19 forward icon'),
    ('SymbolIsPOI() const override { return true; }', 'POI flag'),
    ('IsNonDisplaceable() const override { return true; }', 'non-displaceable'),
    ('GetDepthTestEnabled() const override { return false; }', 'depth test disabled'),
):
    need(fs, token, label)

if 'postPoints(signals, "NET-SIG");' in ms:
    errors.append("unsafe signal-only whole-group publisher remains")

if errors:
    print("CB6 v1.9 AUDIT FAILED")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)
print("CB6 v1.9 AUDIT OK: fresh signals publish before optional POIs; v1.8 renderer/policy preserved")
