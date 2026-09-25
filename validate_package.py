#!/usr/bin/env python3
from pathlib import Path
import ast, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
P=[]; F=[]
def c(v,m): (P if v else F).append(m)
for p in sorted(ROOT.glob('*.py'))+sorted((ROOT/'scripts').glob('*.py')):
    try: ast.parse(p.read_text(encoding='utf-8')); P.append('python syntax '+str(p.relative_to(ROOT)))
    except Exception as e: F.append('python syntax '+str(p.relative_to(ROOT))+': '+str(e))
wf=(ROOT/'.github/workflows/build_cb6_voice_final.yml').read_text(encoding='utf-8')
for token in ('cb6-runtime-final','7113ccb5f086183f8884b2aa4e58c987466b6704','checkout --detach','apply_cb6_v17_ui_voice.py','apply_cb6_v111_signal_dedicated_group.py','apply_cb6_independent_convenience.py','apply_cb6_release_fuzzy.py','apply_cb6_runtime_final.py','apply_cb6_final_hardening.py','apply_cb6_production_identity.py','CB6_V111_AUDIT.py','CB6_CONVENIENCE_AUDIT.py','CB6_FULL_SPEC_AUDIT.py','assembleWebRelease','CB6-Navi-Runtime-Final-arm64.apk'):
    c(token in wf,'runtime workflow '+token)
for obsolete in ('assembleFdroidBeta','CB6-Navi-Ver1.6-NativeSignalReset-arm64.apk'):
    c(obsolete not in wf,'runtime workflow excludes obsolete '+obsolete)
identity=(ROOT/'scripts/apply_cb6_production_identity.py').read_text(encoding='utf-8')
c('CB6_FINAL_STATIC_AUDIT.py' in identity,'production identity enforces final cross-feature audit')
hard=(ROOT/'scripts/apply_cb6_final_hardening.py').read_text(encoding='utf-8')
for token in ('mCb6StartupLocationRetryCount < 20','mCb6StartupHeadingApplied','launchCb6VoiceFallback','resolveActivity'):
    c(token in hard,'final hardening '+token)
patch=(ROOT/'scripts/apply_cb6_complete.py').read_text(encoding='utf-8')
for msg,ok in (
 ('own-position SVG untouched','current-position.svg' not in patch),('own-position C++ untouched','my_position.cpp' not in patch),('no forced Japanese','Locale.JAPAN' not in patch),('unsafe entrance selector absent','[entrance][addr:housenumber]' not in patch),('mapping file untouched','mapcss-mapping.csv' not in patch),('priority files untouched','priorities_4_overlays' not in patch),('isolated mark type','CB6_DRIVING' in patch),('native mark creation','CreateUserMark<Cb6DrivingMark>' in patch)):
    c(ok,msg)
required={'cb6-convenience.svg','cb6-daily.svg','cb6-familymart.svg','cb6-lawson.svg','cb6-ministop.svg','cb6-mybasket.svg','cb6-seicomart.svg','cb6-seven.svg','cb6-signal.svg','cb6-signal-s.svg','cb6-signal-m.svg','cb6-signal-l.svg','cb6-stop.svg','cb6-stop-l.svg'}
for theme in ('light','dark'):
    files=list((ROOT/'icons'/theme).glob('*.svg')); names={p.name for p in files}
    c(names==required,theme+' exact runtime icon set (14)')
    for p in files:
        try: ET.parse(p); P.append('SVG '+theme+'/'+p.name)
        except Exception as e: F.append('SVG '+str(p)+': '+str(e))

for doc in ('docs/CB6_COMAPS_ARCHITECTURE.md','docs/CB6_CHANGE_IMPACT_MAP.md','docs/CB6_FROZEN_FEATURES.md','docs/CB6_KNOWN_FAILURES_AND_PROCESS.md'):
    p=ROOT/doc
    c(p.exists() and p.stat().st_size>500,'canonical CB6 development record '+doc)
print(f'PACKAGE_CHECKS={len(P)+len(F)} PASS={len(P)} FAIL={len(F)}')
for x in P: print('PASS',x)
for x in F: print('FAIL',x)
if F: raise SystemExit(1)
