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
require(collector, "dataSource.ForEachInRect(", "DataSource MWM iteration missing")
require(header, "DataSource const & dataSource", "public DataSource collector boundary missing")
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

print("CB6 CONVENIENCE AUDIT PASS: native MWM DataSource collector is read-only, offline and signal-independent")

APPLY = ROOT / "v2/poi/apply_convenience_mwm_diagnostic.py"
if not APPLY.is_file():
    raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: diagnostic apply script missing")
apply = APPLY.read_text(encoding="utf-8")
for token in ("nativeCb6ConvenienceDiagnostic", "CollectConveniencePois", "convenience_mwm_collector.cpp", "CB6 MWM CONVENIENCE:", "onLocationUpdated(@NonNull Location location)", "location.getLatitude()", "location.getLongitude()", "1200, 17"):
    require(apply, token, "diagnostic bridge missing " + token)
for forbidden in ("overpass-api.de", "overpass.kumi.systems", "nativeSetCb6DrivingMarks", "CreateUserMark", "CB6_SIGNAL", "getSavedLocation()"):
    if forbidden in apply:
        raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: diagnostic bridge ownership crossing: " + forbidden)

FINAL = ROOT / "v2/poi/apply_convenience_brand_render.py"
if not FINAL.is_file():
    raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: final renderer apply script missing")
final = FINAL.read_text(encoding="utf-8")
for token in (
    "UserMark::Type::CONVENIENCE",
    "nativeCb6CollectConvenienceMarks",
    "CollectConveniencePois",
    "nativeSetCb6ConvenienceMarks",
    "mCb6ConvenienceLastLocation",
    "distanceTo(mCb6ConvenienceLastLocation) >= 800.0f",
    "cb6-seven", "cb6-familymart", "cb6-lawson", "cb6-seicomart",
    "cb6-mybasket", "cb6-ministop", "cb6-daily",
    'for theme in ("light", "dark")',
    'caption_selector = "node|z18-[shop=convenience],\\n"',
    'style.count(caption_selector) != 2:',
    'style.count(icon_rule) != 1',
    'style.count(size_rule) != 1',
    'style = style.replace(caption_selector, "", 1)',
    'style = style.replace(icon_rule, "", 1)',
    'style = style.replace(size_rule, "", 1)',
    'if "shop=convenience" in style:',
):
    require(final, token, "final renderer missing " + token)
for forbidden in ("overpass-api.de", "overpass.kumi.systems", "nativeSetCb6DrivingMarks"):
    if forbidden in final:
        raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: final renderer ownership crossing: " + forbidden)

# Integrated build may preserve the already-applied Signal UserMark enum while adding
# CONVENIENCE. CB6_SIGNAL is permitted only in these exact coexistence anchors; any
# other Signal dependency in the convenience renderer remains fail-closed.
allowed_signal_anchors = (
    'signal_old = "    TRAFFIC_LIGHT,\\n    CB6_SIGNAL,\\n    USER_MARK_TYPES_COUNT,"',
    'signal_new = "    TRAFFIC_LIGHT,\\n    CONVENIENCE,\\n    CB6_SIGNAL,\\n    USER_MARK_TYPES_COUNT,"',
)
signal_scrubbed = final
for anchor in allowed_signal_anchors:
    require(final, anchor, "integrated Signal/Convenience coexistence anchor missing")
    if final.count(anchor) != 1:
        raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: coexistence anchor count changed")
    signal_scrubbed = signal_scrubbed.replace(anchor, "")
if "CB6_SIGNAL" in signal_scrubbed:
    raise SystemExit("CB6 CONVENIENCE AUDIT FAIL: final renderer Signal dependency outside coexistence anchor")
print("CB6 CONVENIENCE FINAL RENDER AUDIT PASS: dedicated MWM-backed group, symbols and refresh are signal-independent")
