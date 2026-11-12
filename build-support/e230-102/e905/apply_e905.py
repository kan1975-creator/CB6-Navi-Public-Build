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
