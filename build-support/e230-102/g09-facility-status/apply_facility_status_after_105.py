#!/usr/bin/env python3
"""G09: replace only the stage211 facility status Repository after stage105."""
from pathlib import Path
import hashlib
import sys

REL = Path('android/app/src/main/java/app/organicmaps/cb6/data/Cb6DataStatusRepository.java')
OLD = '52a1455515208f52a6208a2265c5d4515a48308d2dd4873e8680bdab44f2b4f7'
NEW = '39f653a1c772c23f06fc55b25cfb9d4798e6e1f085ecd06f44e20b75d960d3cd'
if len(sys.argv) != 3:
    raise SystemExit('STOP: usage apply_facility_status_after_105.py COMAPS_ROOT FIXED_JAVA')
root, source = Path(sys.argv[1]), Path(sys.argv[2])
target = root / REL
if (not root.is_dir() or target.is_symlink() or not target.is_file()
        or source.is_symlink() or not source.is_file()):
    raise SystemExit('STOP: missing or unsafe source/target')
sha = lambda data: hashlib.sha256(data).hexdigest()
old_bytes, new_bytes = target.read_bytes(), source.read_bytes()
if sha(old_bytes) != OLD or sha(new_bytes) != NEW:
    raise SystemExit('STOP: Repository original/candidate SHA-256 mismatch; no changes made')
if old_bytes.count(b'private Status facilityStatus()') != 1 or new_bytes.count(b'private Status facilityStatus()') != 1:
    raise SystemExit('STOP: Repository anchor mismatch; no changes made')
if b'Cb6FacilityStatusContract.read(context)' not in old_bytes or b'PRAGMA quick_check(1)' not in new_bytes:
    raise SystemExit('STOP: facility status anchor mismatch; no changes made')
target.write_bytes(new_bytes)
print('PASS: G09 facility status Repository only applied after stage105')
