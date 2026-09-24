#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
s = fw.read_text(encoding="utf-8")

# Real-device correction: the pinned CoMaps 500 m class is below z15.
# Preserve acquisition, renderer, 200 m sizing, and forward emphasis; only
# extend the normal slim signal one zoom level outward. 1 km remains hidden.
old_symbol = 'symbols->insert({15, "cb6-signal"});'
old_min = 'int GetMinZoom() const override { return 15; }'
new_symbol = 'symbols->insert({14, "cb6-signal"});'
new_min = 'int GetMinZoom() const override { return 14; }'

start = s.find('class Cb6SignalMark final : public DebugMarkPoint')
end = s.find('    };', start)
if start < 0 or end < 0:
    raise SystemExit("Cb6SignalMark class not found")
block = s[start:end]

if old_symbol in block:
    block = block.replace(old_symbol, new_symbol, 1)
elif new_symbol not in block and 'symbols->insert({14, "cb6-signal-xs"});' not in block:
    raise SystemExit("signal normal zoom anchor not found")
if old_min in block:
    block = block.replace(old_min, new_min, 1)
elif new_min not in block:
    raise SystemExit("signal minimum zoom anchor not found")

s = s[:start] + block + s[end:]
fw.write_text(s, encoding="utf-8")
print("CB6 500m signal visibility applied: normal slim signal from z14; 200m/forward emphasis preserved")