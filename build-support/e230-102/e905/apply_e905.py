#!/usr/bin/env python3
"""Apply E900 C++/JNI and E905 Java after their exact baselines; no network."""
import hashlib,json,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit('usage: apply_e905.py COMAPS_ROOT')
root=Path(sys.argv[1]).resolve();here=Path(__file__).resolve().parent
manifest=json.loads((here/'manifest.json').read_text());updates=[]
for rel,entry in manifest.items():
 dst=root/rel;src=here/'candidate'/rel
 if not dst.is_file() or not src.is_file():raise SystemExit('STOP_MISSING '+rel)
 expected=entry.get('expected_post_e856_sha256',entry.get('expected_post_e230_sha256'))
 if hashlib.sha256(dst.read_bytes()).hexdigest()!=expected:raise SystemExit('STOP_BASE_SHA_MISMATCH '+rel)
 data=src.read_bytes()
 if hashlib.sha256(data).hexdigest()!=entry['replacement_sha256']:raise SystemExit('STOP_CANDIDATE_SHA_MISMATCH '+rel)
 updates.append((dst,data))
for dst,data in updates:
 dst.write_bytes(data)
 print('APPLIED',dst.relative_to(root))
print('E905_APPLY_PASS')

# Offline graph topology is prepared once at build time and bundled in the APK.
graph=here/'graph'
java_dir=root/'android/app/src/main/java/app/organicmaps/cb6/signals'
provider=java_dir/'SQLiteSignalProvider.java'
text=provider.read_text()
anchor='    return new SignalSnapshot(points,members,centers);'
if text.count(anchor)!=1:raise SystemExit('Graph topology provider anchor changed')
provider.write_text(text.replace(anchor,'    GraphSignalTopology.apply(context,points,members,centers);\n'+anchor))
(java_dir/'GraphSignalTopology.java').write_bytes((graph/'GraphSignalTopology.java').read_bytes())
assets=root/'android/app/src/main/assets'
assets.mkdir(parents=True,exist_ok=True)
(assets/'cb6_graph_topology.csv').write_bytes((graph/'cb6_graph_topology.csv').read_bytes())
print('Offline road graph topology connected to existing snapshot member/center IDs')

