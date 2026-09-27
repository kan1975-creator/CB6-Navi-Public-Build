#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "v2/poi/native/convenience_mwm_collector.cpp"
HEADER = ROOT / "v2/poi/native/convenience_mwm_collector.hpp"
CLASSIFIER = ROOT / "v2/poi/native/convenience_brand_classifier.cpp"

def require(text, token, label):
    if token not in text:
        raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: " + label)

for path in (COLLECTOR, HEADER, CLASSIFIER):
    if not path.is_file():
        raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: missing " + str(path.relative_to(ROOT)))

collector = COLLECTOR.read_text(encoding="utf-8")
header = HEADER.read_text(encoding="utf-8")

require(collector, 'GetTypeByPathSafe({"shop", "convenience"})', "native shop=convenience classificator path missing")
require(collector, "fetcher.ForEachFeature(rect", "FeaturesFetcher MWM iteration missing")
require(collector, "FMD_BRAND", "brand metadata evidence missing")
require(collector, "FMD_OPERATOR", "operator metadata evidence missing")
require(collector, "ClassifyConvenience(", "brand classifier integration missing")
require(header, "std::vector<ConveniencePoi> CollectConveniencePois", "collector interface missing")

for forbidden in (
    "overpass-api.de",
    "overpass.kumi.systems",
    "nativeSetCb6DrivingMarks",
    "CreateUserMark",
    "CB6_SIGNAL",
):
    if forbidden in collector or forbidden in header:
        raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: forbidden ownership crossing: " + forbidden)

print("CB6 CONVENIENCE AUDIT PASS: native MWM collector is read-only, offline and signal-independent")

APPLY = ROOT / "v2/poi/apply_convenience_mwm_diagnostic.py"
if not APPLY.is_file():
    raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: diagnostic apply script missing")
apply = APPLY.read_text(encoding="utf-8")
for token in ("nativeCb6ConvenienceDiagnostic", "CollectConveniencePois", "convenience_mwm_collector.cpp"):
    require(apply, token, "diagnostic bridge missing " + token)
for forbidden in ("overpass-api.de", "overpass.kumi.systems", "nativeSetCb6DrivingMarks", "CreateUserMark", "CB6_SIGNAL"):
    if forbidden in apply:
        raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: diagnostic bridge ownership crossing: " + forbidden)
