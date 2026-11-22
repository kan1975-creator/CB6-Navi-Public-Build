#!/usr/bin/env python3
"""Apply G09 sources only in a disposable CoMaps checkout AFTER convenience overlay."""
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: apply_g09_integrated.py <disposable-comaps-root>')
root=Path(sys.argv[1]).resolve(); here=Path(__file__).resolve().parent
for rel in ['android/app/src/main/java/app/organicmaps/MwmActivity.java','android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp','android/sdk/src/main/java/app/organicmaps/sdk/Framework.java']:
 if not (root/rel).is_file(): raise SystemExit('STOP: missing CoMaps overlay source '+rel)
# Strict order: reset patches original lifecycle and JNI; SQLite patches reset-adjusted lifecycle.
for name in ['apply_g09_convenience_reset.py','apply_g09_sqlite_single_source.py','apply_g09_viewport_native.py','g09_apply_native_diff.py']:
 subprocess.run([sys.executable,str(here/name),str(root)],check=True)
print('G09_INTEGRATED_SOURCE_APPLIED: JNI/Java transformations only; stage bundled SQLite separately')
