#!/usr/bin/env python3
"""Fail-closed staging for fixed 14,934-row G09 facility SQLite. No replacement."""
import hashlib, sqlite3, shutil, sys
from pathlib import Path
EXPECTED = "c34b6002deb6e57675616154615ddfbfaa3198b777e30b76928bf6e9b2daa76c"
if len(sys.argv) != 3:
    raise SystemExit("usage: stage_facility_db_14934.py <sqlite-file> <restored-comaps-root>")
src, root = Path(sys.argv[1]), Path(sys.argv[2])
dst = root / "android/app/src/main/assets/cb6_facilities.sqlite"
if not src.is_file(): raise SystemExit("STOP_MISSING_SQLITE")
if hashlib.sha256(src.read_bytes()).hexdigest() != EXPECTED:
    raise SystemExit("STOP_SQLITE_SHA_MISMATCH")
with sqlite3.connect(f"file:{src.resolve()}?mode=ro", uri=True) as db:
    if db.execute("PRAGMA quick_check").fetchone() != ("ok",):
        raise SystemExit("STOP_SQLITE_INTEGRITY")
    if db.execute("SELECT schema_version FROM cb6_metadata").fetchall() != [(1,)]:
        raise SystemExit("STOP_SCHEMA_VERSION")
    if db.execute("SELECT count(*) FROM facilities").fetchone() != (14934,):
        raise SystemExit("STOP_ROW_COUNT")
    if db.execute("SELECT count(*) FROM facilities WHERE category='roadside_station'").fetchone() != (128,):
        raise SystemExit("STOP_ROADSIDE_COUNT")
if not dst.parent.is_dir(): raise SystemExit("STOP_ANDROID_ASSETS_DIR_MISSING")
if dst.exists(): raise SystemExit("STOP_ASSET_ALREADY_EXISTS")
shutil.copyfile(src, dst)
print("G09_FACILITY_14934_STAGED", dst)
