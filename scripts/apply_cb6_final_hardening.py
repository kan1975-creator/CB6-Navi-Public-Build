#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve()
def read(rel):
 p=ROOT/rel
 if not p.exists(): raise SystemExit('missing: '+rel)
 return p.read_text(encoding='utf-8')
def write(rel,s):(ROOT/rel).write_text(s,encoding='utf-8');print('final hardening:',rel)

rel='android/app/src/main/java/app/organicmaps/MwmActivity.java';s=read(rel)
field='  private boolean mCb6StartupHeadingPending = false;\n'
if 'mCb6StartupLocationRetryCount' not in s:
 if field not in s: raise SystemExit('startup heading field anchor missing')
 s=s.replace(field,field+'  private int mCb6StartupLocationRetryCount = 0;\n  private boolean mCb6StartupHeadingApplied = false;\n',1)
start=s.find('  private void scheduleCb6StartupLocationMode()\n');end=s.find('  private void applyCb6StartupHeadingIfReady()\n',start)
if start<0 or end<0: raise SystemExit('startup helper block not found')
new='''  private void scheduleCb6StartupLocationMode()\n  {\n    mCb6StartupLocationRetryCount = 0;\n    mCb6StartupHeadingApplied = false;\n    scheduleCb6StartupLocationAttempt(350L);\n  }\n\n  private void scheduleCb6StartupLocationAttempt(long delayMs)\n  {\n    final View decor = getWindow().getDecorView();\n    decor.postDelayed(() -> {\n      if (!Map.isEngineCreated())\n      {\n        if (++mCb6StartupLocationRetryCount < 20)\n          scheduleCb6StartupLocationAttempt(500L);\n        return;\n      }\n      try\n      {\n        final int mode = LocationState.getMode();\n        if (mode == LocationState.NOT_FOLLOW_NO_POSITION || mode == LocationState.NOT_FOLLOW)\n        {\n          mCb6StartupHeadingPending = true;\n          LocationState.nativeStartPendingPositionMode();\n        }\n        else if (mode == FOLLOW)\n        {\n          mCb6StartupHeadingPending = true;\n          applyCb6StartupHeadingIfReady();\n        }\n        else if (mode == FOLLOW_AND_ROTATE)\n        {\n          mCb6StartupHeadingPending = false;\n          mCb6StartupHeadingApplied = true;\n        }\n      }\n      catch (RuntimeException e)\n      {\n        Logger.w(TAG, "CB6 startup location mode unavailable", e);\n        if (++mCb6StartupLocationRetryCount < 20)\n          scheduleCb6StartupLocationAttempt(500L);\n      }\n    }, delayMs);\n  }\n\n'''
s=s[:start]+new+s[end:]
old='''  private void applyCb6StartupHeadingIfReady()\n  {\n    if (!mCb6StartupHeadingPending || !Map.isEngineCreated())\n      return;'''
new2='''  private void applyCb6StartupHeadingIfReady()\n  {\n    if (mCb6StartupHeadingApplied || !mCb6StartupHeadingPending || !Map.isEngineCreated())\n      return;'''
if old in s:s=s.replace(old,new2,1)
elif 'mCb6StartupHeadingApplied || !mCb6StartupHeadingPending' not in s: raise SystemExit('heading apply method anchor missing')
if 'LocationState.nativeSwitchToNextMode();\n        mCb6StartupHeadingPending = false;\n        mCb6StartupHeadingApplied = true;' not in s:
 s=s.replace('LocationState.nativeSwitchToNextMode();\n        mCb6StartupHeadingPending = false;','LocationState.nativeSwitchToNextMode();\n        mCb6StartupHeadingPending = false;\n        mCb6StartupHeadingApplied = true;',1)
for token in ('mCb6StartupLocationRetryCount < 20','scheduleCb6StartupLocationAttempt(500L);','mCb6StartupHeadingApplied = true;','mCb6StartupHeadingApplied || !mCb6StartupHeadingPending'):
 if token not in s: raise SystemExit('startup hardening missing: '+token)
write(rel,s)

rel='android/app/src/main/java/app/organicmaps/search/SearchFragment.java';s=read(rel)
field='  private Intent mCb6PendingVoiceIntent;\n'
if 'mCb6ActiveFallbackIntent' not in s:
 if field not in s: raise SystemExit('voice pending intent field anchor missing')
 s=s.replace(field,field+'  @Nullable\n  private Intent mCb6ActiveFallbackIntent;\n  private boolean mCb6VoiceFallbackAttempted;\n',1)
s=s.replace('''    if (!SpeechRecognizer.isRecognitionAvailable(requireContext()))\n    {\n      startVoiceRecognitionForResult.launch(fallbackIntent);\n      return;\n    }''','''    if (!SpeechRecognizer.isRecognitionAvailable(requireContext()))\n    {\n      launchCb6VoiceFallback(fallbackIntent);\n      return;\n    }''',1)
anchor='''    if (mCb6SpeechRecognizer != null)\n      mCb6SpeechRecognizer.destroy();\n''';replacement='''    mCb6ActiveFallbackIntent = fallbackIntent;\n    mCb6VoiceFallbackAttempted = false;\n    if (mCb6SpeechRecognizer != null)\n      mCb6SpeechRecognizer.destroy();\n'''
if 'mCb6ActiveFallbackIntent = fallbackIntent;' not in s:
 if anchor not in s: raise SystemExit('voice recognizer reset anchor missing')
 s=s.replace(anchor,replacement,1)
s=s.replace('@Override public void onError(int error) {}','''@Override public void onError(int error)\n      {\n        if (!mCb6VoiceFallbackAttempted && mCb6ActiveFallbackIntent != null)\n        {\n          mCb6VoiceFallbackAttempted = true;\n          launchCb6VoiceFallback(mCb6ActiveFallbackIntent);\n        }\n      }''',1)
method_anchor='  private final ActivityResultLauncher<Intent> mContactPickerLauncher =\n';helper='''  private void launchCb6VoiceFallback(@NonNull Intent intent)\n  {\n    if (intent.resolveActivity(requireContext().getPackageManager()) != null)\n      startVoiceRecognitionForResult.launch(intent);\n    else\n      android.util.Log.w("CB6Voice", "No speech recognition service or fallback activity is installed");\n  }\n\n'''
if 'private void launchCb6VoiceFallback' not in s:
 if method_anchor not in s: raise SystemExit('voice fallback helper anchor missing')
 s=s.replace(method_anchor,helper+method_anchor,1)
for token in ('launchCb6VoiceFallback(fallbackIntent);','mCb6ActiveFallbackIntent = fallbackIntent;','@Override public void onError(int error)','intent.resolveActivity(requireContext().getPackageManager()) != null'):
 if token not in s: raise SystemExit('voice hardening missing: '+token)
write(rel,s)
print('CB6 final hardening applied/reapplied safely')
