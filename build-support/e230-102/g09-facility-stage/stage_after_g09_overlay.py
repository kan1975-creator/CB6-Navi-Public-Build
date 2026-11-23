#!/usr/bin/env python3
"""Post-G09, pre-generate_symbols.sh; never rerun convenience installer."""
from io import BytesIO
from pathlib import Path
from hashlib import sha256

from PIL import Image
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
'''if (m_kind == 26 || (m_kind >= 28 && m_kind <= 31))
    {
      symbols->insert({14, symbol});
      symbols->insert({15, symbol});
      symbols->insert({16, symbol});
    }''': '''if (m_kind == 26)
    {
      symbols->insert({18, symbol});
    }''',
'if (kinds[i] == 24 || kinds[i] == 25 || kinds[i] == 27) continue;':'// All facility kinds 24..31 have dedicated symbols; no silent exclusion.',
}
replacements={a.replace('\n','\n'):b.replace('\n','\n') for a,b in replacements.items()}
for old,new in replacements.items():
    if s.count(old)!=1: raise SystemExit('STOP: native anchor missing or ambiguous: '+old[:72])
    s=s.replace(old,new,1)
# Match each zoom variant to the actual six-brand PNG long edge at this density.
densities = ("mdpi", "hdpi", "xhdpi", "6plus", "xxhdpi", "xxxhdpi")
names = ("roadside", "eneos", "park", "public", "supermarket", "department", "airport", "fuel")
assets = []
for theme in ("light", "dark"):
    style = root / "data/styles/default" / theme
    sources = here / "disposable_styles/data/styles/default" / theme / "symbols"
    edges = {}
    for density in densities:
        for suffix in ("", "-85", "-50"):
            with Image.open(style / density / f"cb6-seven{suffix}.png") as brand:
                edges[density, suffix] = max(brand.size)
    for name in names:
        stem = f"cb6-{name}"
        source = sources / f"{stem}.svg"
        # Use density PNGs exclusively, like the six convenience brands.
        suffixes = ("",) if name == "park" else ("", "-85", "-50")
        for suffix in suffixes:
            if (style / "symbols" / f"{stem}{suffix}.svg").exists():
                raise SystemExit(f"STOP: facility SVG collision: {stem}{suffix}")
        # Match the bundled transparent master to the exact source SVG.
        digest = sha256(source.read_bytes()).hexdigest()
        with Image.open(here / "raster_masters" / f"{stem}-{digest}.png") as icon:
            for density in densities:
                for suffix in suffixes:
                    reference = edges[density, suffix]
                    edge = reference if name == "roadside" else max(1, round(reference * 0.85))
                    output = BytesIO()
                    icon.resize((edge, edge), Image.Resampling.LANCZOS).save(output, format="PNG")
                    dest = style / density / f"{stem}{suffix}.png"
                    data = output.getvalue()
                    if dest.exists() and dest.read_bytes() != data:
                        raise SystemExit(f"STOP: facility PNG collision: {dest}")
                    assets.append((dest, data))
repo=(here/'SQLiteFacilityRepository.java').read_text()
for kind in range(24,32):
    if ('return '+str(kind)+';') not in repo: raise SystemExit('STOP: repository kind missing '+str(kind))
# Preflight complete: only disposable checkout is modified.
fw.write_text(s)
java.write_text(repo)
for dest, data in assets:
    dest.write_bytes(data)
print('G09_FACILITY_PRE_ATLAS_STAGED; generator remains in existing Workflow step')
