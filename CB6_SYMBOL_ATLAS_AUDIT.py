#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve()
need=('cb6-signal','cb6-signal-s','cb6-signal-m','cb6-signal-l','cb6-stop','cb6-stop-l','cb6-seven','cb6-familymart','cb6-lawson','cb6-seicomart','cb6-ministop','cb6-daily','cb6-mybasket','cb6-convenience')
atlases=sorted(ROOT.glob('**/symbols.sdf'))
if not atlases:
    raise SystemExit('ATLAS FAIL: no generated symbols.sdf found')
# SDF atlas metadata contains symbol identifiers as byte strings. Require every
# runtime CB6 symbol to be present in generated output, not merely in C++ or SVG.
found={n:[] for n in need}
for p in atlases:
    try: data=p.read_bytes()
    except Exception: continue
    for n in need:
        if n.encode() in data: found[n].append(str(p.relative_to(ROOT)))
missing=[n for n,v in found.items() if not v]
print('ATLAS_FILES='+str(len(atlases)))
for n in need: print(('PASS ' if found[n] else 'FAIL ')+n+(' -> '+','.join(found[n]) if found[n] else ''))
if missing: raise SystemExit('ATLAS FAIL missing: '+', '.join(missing))
print('ATLAS PASS all CB6 runtime symbols present in generated symbols.sdf')
