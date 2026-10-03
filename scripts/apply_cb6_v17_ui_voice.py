#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()


def read(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("missing: " + rel)
    return p.read_text(encoding="utf-8")


def write(rel, s):
    p = ROOT / rel
    p.write_text(s, encoding="utf-8")
    print("v1.7 patched:", rel)


def once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, got {n}")
    return s.replace(old, new, 1)


def once_in_method(s, method_anchor, old, new, label):
    """Replace exactly once inside one Java method, not elsewhere in the class."""
    start = s.find(method_anchor)
    if start < 0:
        raise SystemExit(f"{label}: method anchor missing")
    # The next top-level override/method is a safe boundary in this pinned source.
    candidates = [p for p in (s.find("\n  @Override", start + len(method_anchor)),
                              s.find("\n  @UiThread", start + len(method_anchor)),
                              s.find("\n  private ", start + len(method_anchor)),
                              s.find("\n  public ", start + len(method_anchor))) if p >= 0]
    end = min(candidates) if candidates else len(s)
    block = s[start:end]
    n = block.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match in method, got {n}")
    block = block.replace(old, new, 1)
    return s[:start] + block + s[end:]


# -----------------------------------------------------------------------------
# Stage 2: lower vehicle position; compact/lower road HUD + Google beside it;
# startup returns to current position and switches to heading-up once location is
# available. Existing signal renderer and vehicle icon are deliberately untouched.
# -----------------------------------------------------------------------------
rel = "android/app/src/main/java/app/organicmaps/MwmActivity.java"
s = read(rel)

if "private static final int CB6_POSITION_LOWER_DP = 72;" in s:
    s = s.replace("private static final int CB6_POSITION_LOWER_DP = 72;",
                  "private static final int CB6_POSITION_LOWER_DP = 96;", 1)
elif "private static final int CB6_POSITION_LOWER_DP = 96;" not in s:
    raise SystemExit("vehicle lower-position constant anchor missing")

field_anchor = "  private static final int CB6_POSITION_LOWER_DP = 96;\n"
if "mCb6StartupHeadingPending" not in s:
    s = once(s, field_anchor, field_anchor + "  private boolean mCb6StartupHeadingPending = false;\n", "startup heading field")

s = s.replace("((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 46 : 50);",
              "((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 30 : 34);", 1)

road_tail = '''      mCb6RoadHud.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, landscape ? 12 : 13);\n      if (lp instanceof android.view.ViewGroup.MarginLayoutParams)\n        ((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 30 : 34);\n    }'''
road_new = '''      mCb6RoadHud.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, landscape ? 12 : 13);\n      if (lp instanceof android.view.ViewGroup.MarginLayoutParams)\n        ((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 30 : 34);\n      mCb6RoadHud.setTranslationX(cb6Dp(24));\n    }'''
if road_tail in s:
    s = s.replace(road_tail, road_new, 1)
elif "mCb6RoadHud.setTranslationX(cb6Dp(24));" not in s:
    raise SystemExit("road HUD positioning anchor missing")

s = s.replace("((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 92 : 100);",
              "((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 30 : 34);", 1)

google_tail = '''      mCb6GoogleMaps.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 10);\n      if (lp instanceof android.view.ViewGroup.MarginLayoutParams)\n        ((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 30 : 34);\n    }'''
google_new = '''      mCb6GoogleMaps.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 10);\n      if (lp instanceof android.view.ViewGroup.MarginLayoutParams)\n        ((android.view.ViewGroup.MarginLayoutParams) lp).bottomMargin = cb6Dp(landscape ? 30 : 34);\n      if (lp instanceof android.widget.RelativeLayout.LayoutParams)\n      {\n        android.widget.RelativeLayout.LayoutParams rlp = (android.widget.RelativeLayout.LayoutParams) lp;\n        rlp.removeRule(android.widget.RelativeLayout.ALIGN_PARENT_END);\n        rlp.addRule(android.widget.RelativeLayout.RIGHT_OF, R.id.cb6_road_hud);\n        rlp.setMarginStart(cb6Dp(8));\n        mCb6GoogleMaps.setLayoutParams(rlp);\n      }\n      mCb6GoogleMaps.setTranslationX(cb6Dp(24));\n    }'''
if google_tail in s:
    s = s.replace(google_tail, google_new, 1)
elif "rlp.addRule(android.widget.RelativeLayout.RIGHT_OF, R.id.cb6_road_hud);" not in s:
    raise SystemExit("Google button positioning anchor missing")

render_anchor = "    ThemeSwitcher.INSTANCE.restart(true);\n"
render_add = '''    ThemeSwitcher.INSTANCE.restart(true);\n    scheduleCb6StartupLocationMode();\n'''
if "scheduleCb6StartupLocationMode();" not in s:
    s = once(s, render_anchor, render_add, "startup location schedule call")

helper_anchor = "  private int cb6Dp(int dp)\n"
helper = '''  private void scheduleCb6StartupLocationMode()\n  {\n    final View decor = getWindow().getDecorView();\n    decor.postDelayed(() -> {\n      if (!Map.isEngineCreated())\n        return;\n      try\n      {\n        final int mode = LocationState.getMode();\n        if (mode == LocationState.NOT_FOLLOW_NO_POSITION || mode == LocationState.NOT_FOLLOW)\n        {\n          mCb6StartupHeadingPending = true;\n          LocationState.nativeStartPendingPositionMode();\n        }\n        else if (mode == FOLLOW)\n        {\n          mCb6StartupHeadingPending = true;\n        }\n      }\n      catch (RuntimeException e)\n      {\n        Logger.w(TAG, "CB6 startup location mode unavailable", e);\n      }\n    }, 350L);\n  }\n\n  private void applyCb6StartupHeadingIfReady()\n  {\n    if (!mCb6StartupHeadingPending || !Map.isEngineCreated())\n      return;\n    try\n    {\n      final int mode = LocationState.getMode();\n      if (mode == FOLLOW)\n      {\n        LocationState.nativeSwitchToNextMode();\n        mCb6StartupHeadingPending = false;\n      }\n      else if (mode == FOLLOW_AND_ROTATE)\n      {\n        mCb6StartupHeadingPending = false;\n      }\n    }\n    catch (RuntimeException e)\n    {\n      Logger.w(TAG, "CB6 heading-up switch unavailable", e);\n    }\n  }\n\n'''
if "private void scheduleCb6StartupLocationMode()" not in s:
    s = once(s, helper_anchor, helper + helper_anchor, "startup location helpers")

# There are two dismissLocationErrorDialog() calls in the pinned MwmActivity.
# Apply heading transition only in LocationListener.onLocationUpdated().
if "applyCb6StartupHeadingIfReady();" not in s:
    method_anchor = "  public void onLocationUpdated(@NonNull Location location)\n  {\n"
    loc_anchor = "    dismissLocationErrorDialog();\n"
    s = once_in_method(s, method_anchor, loc_anchor,
                       "    dismissLocationErrorDialog();\n    applyCb6StartupHeadingIfReady();\n",
                       "location heading application")

write(rel, s)

# -----------------------------------------------------------------------------
# Stage 3: Android 13 Japanese voice search through the existing CoMaps query path.
# -----------------------------------------------------------------------------
rel = "android/app/src/main/AndroidManifest.xml"
s = read(rel)
perm_anchor = '  <uses-permission android:name="android.permission.INTERNET"/>\n'
if 'android.permission.RECORD_AUDIO' not in s:
    s = once(s, perm_anchor, perm_anchor + '  <uses-permission android:name="android.permission.RECORD_AUDIO"/>\n', "record audio permission")
query_anchor = '''    <intent>\n      <action android:name="android.intent.action.TTS_SERVICE"/>\n    </intent>\n'''
query_add = query_anchor + '''    <intent>\n      <action android:name="android.speech.action.RECOGNIZE_SPEECH"/>\n    </intent>\n    <intent>\n      <action android:name="android.speech.RecognitionService"/>\n    </intent>\n'''
if 'android.speech.RecognitionService' not in s:
    s = once(s, query_anchor, query_add, "speech queries")
write(rel, s)

rel = "android/app/src/main/java/app/organicmaps/util/InputUtils.java"
s = read(rel)
if "import android.speech.SpeechRecognizer;" not in s:
    s = once(s, "import android.speech.RecognizerIntent;\n",
             "import android.speech.RecognizerIntent;\nimport android.speech.SpeechRecognizer;\n", "SpeechRecognizer import")
s = s.replace(
    "mVoiceInputSupported = Utils.isIntentSupported(context, new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH));",
    "mVoiceInputSupported = SpeechRecognizer.isRecognitionAvailable(context)\n"
    "          || Utils.isIntentSupported(context, new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH));",
    1)
old_intent = '''    final Intent vrIntent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);\n    vrIntent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_WEB_SEARCH)\n        .putExtra(RecognizerIntent.EXTRA_PROMPT, promptText);'''
new_intent = '''    final Intent vrIntent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);\n    vrIntent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_WEB_SEARCH)\n        .putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ja-JP")\n        .putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ja-JP")\n        .putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)\n        .putExtra(RecognizerIntent.EXTRA_PROMPT, promptText);'''
if old_intent in s:
    s = s.replace(old_intent, new_intent, 1)
elif 'RecognizerIntent.EXTRA_LANGUAGE, "ja-JP"' not in s:
    raise SystemExit("voice intent language anchor missing")
write(rel, s)

rel = "android/app/src/main/java/app/organicmaps/search/SearchFragment.java"
s = read(rel)
imports_anchor = "import android.content.Intent;\n"
imports = '''import android.content.Intent;\nimport android.content.pm.PackageManager;\nimport android.os.Build;\nimport android.speech.RecognitionListener;\nimport android.speech.RecognizerIntent;\nimport android.speech.SpeechRecognizer;\n'''
if "import android.speech.SpeechRecognizer;" not in s:
    s = once(s, imports_anchor, imports, "voice imports")
if "import androidx.core.content.ContextCompat;" not in s:
    s = once(s, "import androidx.core.view.ViewCompat;\n",
             "import androidx.core.view.ViewCompat;\nimport androidx.core.content.ContextCompat;\n", "ContextCompat import")

old_start = '''    protected void startVoiceRecognition(Intent intent)\n    {\n      startVoiceRecognitionForResult.launch(intent);\n    }'''
new_start = '''    protected void startVoiceRecognition(Intent intent)\n    {\n      startCb6VoiceRecognition(intent);\n    }'''
if old_start in s:
    s = s.replace(old_start, new_start, 1)
elif "startCb6VoiceRecognition(intent);" not in s:
    raise SystemExit("SearchFragment voice start anchor missing")

launcher_anchor = '''  private final ActivityResultLauncher<Intent> startVoiceRecognitionForResult =\n      registerForActivityResult(new ActivityResultContracts.StartActivityForResult(),\n                                activityResult -> mToolbarController.onVoiceRecognitionResult(activityResult));\n'''
launcher_add = launcher_anchor + '''\n  @Nullable\n  private SpeechRecognizer mCb6SpeechRecognizer;\n  @Nullable\n  private Intent mCb6PendingVoiceIntent;\n  private final ActivityResultLauncher<String> mCb6AudioPermissionLauncher =\n      registerForActivityResult(new ActivityResultContracts.RequestPermission(), granted -> {\n        if (granted && mCb6PendingVoiceIntent != null)\n        {\n          Intent pending = mCb6PendingVoiceIntent;\n          mCb6PendingVoiceIntent = null;\n          startCb6VoiceRecognition(pending);\n        }\n        else\n        {\n          mCb6PendingVoiceIntent = null;\n        }\n      });\n'''
if "mCb6AudioPermissionLauncher" not in s:
    s = once(s, launcher_anchor, launcher_add, "voice permission launcher")

method_anchor = "  private final ActivityResultLauncher<Intent> mContactPickerLauncher =\n"
voice_method = '''  private void startCb6VoiceRecognition(@NonNull Intent fallbackIntent)\n  {\n    if (ContextCompat.checkSelfPermission(requireContext(), android.Manifest.permission.RECORD_AUDIO)\n        != PackageManager.PERMISSION_GRANTED)\n    {\n      mCb6PendingVoiceIntent = fallbackIntent;\n      mCb6AudioPermissionLauncher.launch(android.Manifest.permission.RECORD_AUDIO);\n      return;\n    }\n\n    if (!SpeechRecognizer.isRecognitionAvailable(requireContext()))\n    {\n      startVoiceRecognitionForResult.launch(fallbackIntent);\n      return;\n    }\n\n    if (mCb6SpeechRecognizer != null)\n      mCb6SpeechRecognizer.destroy();\n\n    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S\n        && SpeechRecognizer.isOnDeviceRecognitionAvailable(requireContext()))\n      mCb6SpeechRecognizer = SpeechRecognizer.createOnDeviceSpeechRecognizer(requireContext());\n    else\n      mCb6SpeechRecognizer = SpeechRecognizer.createSpeechRecognizer(requireContext());\n\n    mCb6SpeechRecognizer.setRecognitionListener(new RecognitionListener() {\n      @Override public void onReadyForSpeech(Bundle params) {}\n      @Override public void onBeginningOfSpeech() {}\n      @Override public void onRmsChanged(float rmsdB) {}\n      @Override public void onBufferReceived(byte[] buffer) {}\n      @Override public void onEndOfSpeech() {}\n      @Override public void onError(int error) {}\n      @Override public void onPartialResults(Bundle partialResults) {}\n      @Override public void onEvent(int eventType, Bundle params) {}\n      @Override public void onResults(Bundle results)\n      {\n        ArrayList<String> values = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);\n        if (values != null && !values.isEmpty() && !TextUtils.isEmpty(values.get(0)))\n          mToolbarController.setQuery(values.get(0));\n      }\n    });\n\n    Intent direct = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);\n    direct.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_WEB_SEARCH);\n    direct.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ja-JP");\n    direct.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ja-JP");\n    direct.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3);\n    mCb6SpeechRecognizer.startListening(direct);\n  }\n\n'''
if "private void startCb6VoiceRecognition" not in s:
    s = once(s, method_anchor, voice_method + method_anchor, "direct voice method")

old_destroy = '''  public void onDestroy()\n  {\n    for (RecyclerView v : mAttachedRecyclers)'''
new_destroy = '''  public void onDestroy()\n  {\n    if (mCb6SpeechRecognizer != null)\n    {\n      mCb6SpeechRecognizer.destroy();\n      mCb6SpeechRecognizer = null;\n    }\n    for (RecyclerView v : mAttachedRecyclers)'''
if old_destroy in s:
    s = s.replace(old_destroy, new_destroy, 1)
elif "mCb6SpeechRecognizer.destroy();" not in s:
    raise SystemExit("SearchFragment destroy anchor missing")
write(rel, s)

print("CB6 Navi v1.7 UI/startup + Android 13 Japanese voice search applied without changing v1.6 signal rendering.")
