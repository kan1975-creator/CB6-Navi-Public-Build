#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

def text(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("missing: " + rel)
    return p.read_text(encoding="utf-8")

activity = text("android/app/src/main/java/app/organicmaps/MwmActivity.java")
manifest = text("android/app/src/main/AndroidManifest.xml")
input_utils = text("android/app/src/main/java/app/organicmaps/util/InputUtils.java")
search = text("android/app/src/main/java/app/organicmaps/search/SearchFragment.java")
fw = text("android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp")
user = text("libs/map/user_mark.cpp")

required_activity = [
    "CB6_POSITION_LOWER_DP = 96",
    "mCb6RoadHud.setTranslationX(cb6Dp(24));",
    "rlp.addRule(android.widget.RelativeLayout.RIGHT_OF, R.id.cb6_road_hud);",
    "scheduleCb6StartupLocationMode();",
    "applyCb6StartupHeadingIfReady();",
    "LocationState.nativeStartPendingPositionMode();",
    "LocationState.nativeSwitchToNextMode();",
]
required_manifest = [
    "android.permission.RECORD_AUDIO",
    "android.speech.action.RECOGNIZE_SPEECH",
    "android.speech.RecognitionService",
]
required_input = [
    "SpeechRecognizer.isRecognitionAvailable(context)",
    'RecognizerIntent.EXTRA_LANGUAGE, "ja-JP"',
    "RecognizerIntent.EXTRA_MAX_RESULTS, 3",
]
required_search = [
    "startCb6VoiceRecognition(intent);",
    "SpeechRecognizer.isOnDeviceRecognitionAvailable(requireContext())",
    "SpeechRecognizer.createOnDeviceSpeechRecognizer(requireContext())",
    "SpeechRecognizer.createSpeechRecognizer(requireContext())",
    "mCb6AudioPermissionLauncher",
    'RecognizerIntent.EXTRA_LANGUAGE, "ja-JP"',
    "mToolbarController.setQuery(values.get(0));",
]
required_signal = [
    "class Cb6SignalMark final : public DebugMarkPoint",
    "SymbolIsPOI() const override { return true; }",
    "IsNonDisplaceable() const override { return true; }",
    "GetDepthTestEnabled() const override { return false; }",
]

for label, src, items in [
    ("activity", activity, required_activity),
    ("manifest", manifest, required_manifest),
    ("InputUtils", input_utils, required_input),
    ("SearchFragment", search, required_search),
    ("signal renderer", fw, required_signal),
]:
    missing = [x for x in items if x not in src]
    if missing:
        raise SystemExit(label + " missing: " + ", ".join(missing))

# Signal policy must remain authoritative and native MapCSS rendering disabled.
for p in sorted((ROOT / "data/styles").glob("*/include/Icons.mapcss")):
    s = p.read_text(encoding="utf-8")
    if "[highway=traffic_signals]" in s:
        raise SystemExit("native signal MapCSS returned in " + str(p.relative_to(ROOT)))

# Convenience marks remain brand-specific and untouched by the voice/UI stage.
for name in ("seven", "familymart", "lawson", "seicomart", "ministop", "daily", "mybasket"):
    if f'cb6-{name}' not in user:
        raise SystemExit("brand mark missing: " + name)

# Guard against duplicated v1.7 injections.
for needle, expected in [
    ("private void scheduleCb6StartupLocationMode()", 1),
    ("private void startCb6VoiceRecognition", 1),
    ("android.permission.RECORD_AUDIO", 1),
    ("android.speech.RecognitionService", 1),
]:
    sources = activity + search + manifest
    if sources.count(needle) != expected:
        raise SystemExit(f"duplicate/missing marker {needle}: {sources.count(needle)}")

print("CB6 v1.7 audit OK: signal path preserved; UI/startup and Japanese voice-search path present.")
