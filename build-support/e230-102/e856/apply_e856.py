#!/usr/bin/env python3
"""Apply E855 after E774 only; exact SHA-256 guards and all-or-nothing preflight."""
from pathlib import Path
import hashlib,json,sys
if len(sys.argv)!=2: raise SystemExit("usage: apply_e856.py COMAPS_ROOT")
root=Path(sys.argv[1]).resolve()
bundle=Path(__file__).resolve().parent
manifest=json.loads((bundle/"manifest.json").read_text())
updates=[]
for relative,meta in manifest.items():
    target=root/relative
    replacement=bundle/"candidate"/relative
    if not target.is_file() or not replacement.is_file(): raise SystemExit("STOP_MISSING "+relative)
    actual=hashlib.sha256(target.read_bytes()).hexdigest()
    new=hashlib.sha256(replacement.read_bytes()).hexdigest()
    if actual!=meta["expected_post_e774_sha256"]: raise SystemExit("STOP_BASE_SHA_MISMATCH "+relative+" "+actual)
    if new!=meta["replacement_sha256"]: raise SystemExit("STOP_CANDIDATE_SHA_MISMATCH "+relative)
    updates.append((target,replacement.read_bytes()))
for target,data in updates:
    target.write_bytes(data)
    print("APPLIED",target.relative_to(root))
print("E856_APPLY_PASS")
