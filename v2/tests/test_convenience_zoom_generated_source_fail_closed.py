#!/usr/bin/env python3
from pathlib import Path
src = Path("v2/poi/apply_convenience_brand_render.py").read_text(encoding="utf-8")
assert src.count("final double[][] cb6 = Framework.nativeCb6CollectConvenienceMarks(") == 1
assert "mCb6ConvenienceZoomDiag" not in src
assert 'CB6-CONVENIENCE-SCALE-DIAG' not in src
assert "nativeGetDrawScale()" not in src
assert 'symbols->insert({14, std::string(symbol) + "-50"});' in src
assert 'symbols->insert({15, std::string(symbol) + "-85"});' in src
assert "symbols->insert({16, symbol});" in src
assert "GetMinZoom() const override { return 14; }" in src
assert '("-85", 0.85)' in src and '("-50", 0.50)' in src
assert "zoom_anchor =" not in src
assert "nativeCb6CollectConvenienceMarks(\\\\n" not in src
print("CONVENIENCE ZOOM GENERATED-SOURCE FAIL-CLOSED PASS")
