#!/usr/bin/env python3
"""Fail-closed, one-file overlay after successful apply_211.py."""
from pathlib import Path
import hashlib
import sys

OLD = '5e7dae6e73b531471a12bd03b3721299199704278cafbaa5bda6852602b8dd54'
NEW = '233d1bd0224b929c5bc6ae55dc3bd9c94a6c560156f2bcfd200db90542b1d381'
REL = Path('android/app/src/main/java/app/organicmaps/settings/Cb6DataStatusFragment.java')
if len(sys.argv) != 3:
    raise SystemExit('STOP: usage apply_105_after_211.py COMAPS_ROOT FIXED_JAVA')
root, source = Path(sys.argv[1]), Path(sys.argv[2])
target = root / REL
if not root.is_dir() or target.is_symlink() or not target.is_file() or source.is_symlink() or not source.is_file():
    raise SystemExit('STOP: required regular file missing/unsafe')
old_bytes, new_bytes = target.read_bytes(), source.read_bytes()
sha = lambda data: hashlib.sha256(data).hexdigest()
if sha(old_bytes) != OLD or sha(new_bytes) != NEW:
    raise SystemExit('STOP: original or candidate SHA-256 mismatch; no changes made')
target.write_bytes(new_bytes)
print('PASS: stage105 Fragment only applied after stage211')
