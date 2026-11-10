#!/usr/bin/env python3
"""Apply E773 candidate only to exact final post-E710 sources; no partial writes."""
import sys, pathlib, hashlib, json
root=pathlib.Path(sys.argv[1]).resolve()
bundle=pathlib.Path(__file__).resolve().parent
manifest=json.loads((bundle/'manifest.json').read_text())['files']
for name, hashes in manifest.items():
    target=root/name
    candidate=bundle/'candidate'/name
    if not target.is_file() or not candidate.is_file():
        raise SystemExit('STOP_MISSING '+name)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=hashes['expected_final_sha256']:
        raise SystemExit('STOP_BASE_SHA_MISMATCH '+name)
    if hashlib.sha256(candidate.read_bytes()).hexdigest()!=hashes['candidate_sha256']:
        raise SystemExit('STOP_CANDIDATE_SHA_MISMATCH '+name)
for name in manifest:
    (root/name).write_bytes((bundle/'candidate'/name).read_bytes())
    print('APPLIED',name)
print('E774_APPLY_PASS')
