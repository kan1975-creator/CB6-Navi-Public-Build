#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve()

def read(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('missing: '+rel)
    return p.read_text(encoding='utf-8')
def write(rel,s):
    (ROOT/rel).write_text(s,encoding='utf-8')
    print('production cleanup:',rel)

# Voice button availability must not depend on an installed RecognitionService.
# Keep the button visible; actual recognition capability is handled on click.
rel='android/app/src/main/java/app/organicmaps/util/InputUtils.java'
s=read(rel)
s=re.sub(r'mVoiceInputSupported\s*=\s*SpeechRecognizer\.isRecognitionAvailable\(context\)\s*\|\|\s*Utils\.isIntentSupported\(context, new Intent\(RecognizerIntent\.ACTION_RECOGNIZE_SPEECH\)\);',
         'mVoiceInputSupported = true; // CB6: voice-search affordance is always visible; capability checked on click.',s,count=1)
if 'mVoiceInputSupported = true; // CB6:' not in s:
    raise SystemExit('voice visibility assignment not found')
write(rel,s)

# Remove production diagnostic toasts/synthetic signal remnants from manager.
rel='android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java'
m=read(rel)
# Remove showStatus calls used only for signal diagnostics; retain Log diagnostics.
m=re.sub(r'^\s*showStatus\([^\n]*\);\s*\n','',m,flags=re.M)
# Remove the helper itself if present.
m=re.sub(r'\n\s*private void showStatus\([^)]*\)\s*\{.*?\n\s*\}\n','\n',m,count=1,flags=re.S)
for forbidden in ('mDiagnosticLat','mDiagnosticLon','postDiagnosticOnly','TEST1件','SIG TEST','Toast.makeText'):
    if forbidden in m:
        raise SystemExit('production diagnostic remains: '+forbidden)
write(rel,m)

# Native synthetic probes are forbidden in production.
fw=read('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp')
for forbidden in ('Cb6SignalDebugProbe','stockCb6->SetKind(21)','testLat = lats[n - 1]'):
    if forbidden in fw:
        raise SystemExit('native diagnostic remains: '+forbidden)
print('CB6 production cleanup applied: voice affordance always visible; diagnostic signal/toast probes absent')
