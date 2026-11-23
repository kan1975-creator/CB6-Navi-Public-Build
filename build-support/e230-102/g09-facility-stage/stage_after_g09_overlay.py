#!/usr/bin/env python3
"""Post-G09, pre-generate_symbols.sh; never rerun convenience installer."""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
here=Path(__file__).resolve().parent
fw=root/'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp'
java=root/'android/app/src/main/java/app/organicmaps/cb6/facilities/SQLiteFacilityRepository.java'
gen=root/'tools/unix/generate_symbols.sh'
if not all(p.is_file() for p in (fw,java,gen,here/'SQLiteFacilityRepository.java')):
    raise SystemExit('STOP: pinned post-G09 prerequisites missing')
s=fw.read_text()
# Exact native anchors from the fixed GitHub installer. Do not reapply the installer.
replacements={
'case 9: symbol = "cb6-daily"; break;\n    case 26: symbol = "park-m"; break;': 'case 9: symbol = "cb6-daily"; break;\n    case 24: symbol = "cb6-roadside"; break;\n    case 25: symbol = "cb6-eneos"; break;\n    case 26: symbol = "cb6-park"; break;\n    case 27: symbol = "cb6-public"; break;',
'case 28: symbol = "supermarket-m"; break;':'case 28: symbol = "cb6-supermarket"; break;',
'case 29: symbol = "department_store-m"; break;':'case 29: symbol = "cb6-department"; break;',
'case 30: symbol = "airport-m"; break;':'case 30: symbol = "cb6-airport"; break;',
'case 31: symbol = "fuel-m"; break;':'case 31: symbol = "cb6-fuel"; break;',
'if (m_kind == 26 || (m_kind >= 28 && m_kind <= 31))':'if (m_kind >= 24 && m_kind <= 31)',
'if (kinds[i] == 24 || kinds[i] == 25 || kinds[i] == 27) continue;':'// All facility kinds 24..31 have dedicated symbols; no silent exclusion.',
}
replacements={a.replace('\n','\n'):b.replace('\n','\n') for a,b in replacements.items()}
for old,new in replacements.items():
    if s.count(old)!=1: raise SystemExit('STOP: native anchor missing or ambiguous: '+old[:72])
    s=s.replace(old,new,1)
assets=[]
for theme in ('light','dark'):
    for name in ('roadside','eneos','park','public','supermarket','department','airport','fuel'):
        source=here/'disposable_styles/data/styles/default'/theme/'symbols'/('cb6-'+name+'.svg')
        dest=root/'data/styles/default'/theme/'symbols'/source.name
        if not source.is_file() or not dest.parent.is_dir(): raise SystemExit('STOP: symbol source/destination missing '+str(source))
        if dest.exists() and dest.read_bytes()!=source.read_bytes(): raise SystemExit('STOP: symbol collision '+str(dest))
        assets.append((source,dest))
repo=(here/'SQLiteFacilityRepository.java').read_text()
for kind in range(24,32):
    if ('return '+str(kind)+';') not in repo: raise SystemExit('STOP: repository kind missing '+str(kind))
# Preflight complete: only disposable checkout is modified.
fw.write_text(s)
java.write_text(repo)
for source,dest in assets: dest.write_bytes(source.read_bytes())
print('G09_FACILITY_PRE_ATLAS_STAGED; generator remains in existing Workflow step')
