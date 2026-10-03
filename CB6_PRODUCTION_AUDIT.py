#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve()
P=[];F=[]
def check(v,m):(P if v else F).append(m)
def text(rel):
 p=ROOT/rel
 if not p.exists(): F.append('missing '+rel); return ''
 return p.read_text(encoding='utf-8',errors='replace')
input_utils=text('android/app/src/main/java/app/organicmaps/util/InputUtils.java')
search=text('android/app/src/main/java/app/organicmaps/search/SearchFragment.java')
mgr=text('android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java')
fw=text('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp')
check('mVoiceInputSupported = true; // CB6:' in input_utils,'voice search affordance always visible')
check('startCb6VoiceRecognition' in search,'voice click capability path present')
check('SpeechRecognizer.isRecognitionAvailable' in search,'recognition capability checked on click')
for token in ('mDiagnosticLat','mDiagnosticLon','postDiagnosticOnly','TEST1件','SIG TEST','Toast.makeText'):
 check(token not in mgr,'production manager excludes '+token)
for token in ('Cb6SignalDebugProbe','stockCb6->SetKind(21)','testLat = lats[n - 1]'):
 check(token not in fw,'production native excludes '+token)
print(f'PRODUCTION_CHECKS={len(P)+len(F)} PASS={len(P)} FAIL={len(F)}')
for x in P: print('PASS',x)
for x in F: print('FAIL',x)
if F: raise SystemExit(1)
