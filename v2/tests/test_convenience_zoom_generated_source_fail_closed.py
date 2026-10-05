#!/usr/bin/env python3
from pathlib import Path
src = Path("v2/poi/apply_convenience_brand_render.py").read_text(encoding="utf-8")
assert src.count("final double[][] cb6 = Framework.nativeCb6CollectConvenienceMarks(") == 1
assert src.count("mCb6ConvenienceZoomDiagHandler.post(mCb6ConvenienceZoomDiag);") == 1
assert "zoom_anchor =" not in src
assert "nativeCb6CollectConvenienceMarks(\\\\n" not in src
print("CONVENIENCE ZOOM GENERATED-SOURCE FAIL-CLOSED PASS")
