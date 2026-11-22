#!/usr/bin/env python3
"""Stage the already verified G09 SQLite into the restored CoMaps APK assets.
Offline-only, fail closed, no overwrite, no GitHub/Actions operations.
"""
import hashlib, sqlite3, shutil, sys
from pathlib import Path
EXPECTED='d11c6e37b22f47de7283b888e1ce3f7d82fc98ba350cb929abd422029c49f54e'
if len(sys.argv)!=3:
    raise SystemExit('usage: g09_prepare_bundled_db.py <sqlite-file> <restored-comaps-root>')
src=Path(sys.argv[1]); root=Path(sys.argv[2]); dst=root/'android/app/src/main/assets/cb6_facilities.sqlite'
if not src.is_file(): raise SystemExit('STOP_MISSING_SQLITE')
if hashlib.sha256(src.read_bytes()).hexdigest()!=EXPECTED: raise SystemExit('STOP_SQLITE_SHA_MISMATCH')
with sqlite3.connect(f'file:{src.resolve()}?mode=ro',uri=True) as db:
    if db.execute('PRAGMA quick_check').fetchone() != ('ok',): raise SystemExit('STOP_SQLITE_INTEGRITY')
    if db.execute('SELECT schema_version FROM cb6_metadata').fetchall()!=[(1,)]: raise SystemExit('STOP_SCHEMA_VERSION')
    if db.execute('SELECT count(*) FROM facilities').fetchone()!=(2329,): raise SystemExit('STOP_ROW_COUNT')
if not dst.parent.is_dir(): raise SystemExit('STOP_ANDROID_ASSETS_DIR_MISSING')
if dst.exists(): raise SystemExit('STOP_ASSET_ALREADY_EXISTS')
shutil.copyfile(src,dst)
print('G09_BUNDLED_DB_STAGED',dst)
