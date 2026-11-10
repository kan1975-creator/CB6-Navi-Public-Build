#!/usr/bin/env python3
"""Apply E710 heading-refresh throttle only after the offline stage. Fail closed."""
from pathlib import Path
import subprocess
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: apply_e712_after_offline.py COMAPS_ROOT E710_PATCH')
root = Path(sys.argv[1]).resolve()
patch = Path(sys.argv[2]).resolve()
target = root / 'android/app/src/main/java/app/organicmaps/cb6/signals/SignalController.java'
if not target.is_file() or not patch.is_file():
    raise SystemExit('STOP: target or patch missing')
src = target.read_text(encoding='utf-8')
if 'this.provider = new SQLiteSignalProvider(this.context);' not in src:
    raise SystemExit('STOP: offline-only provider not yet applied')
if 'HEADING_REFRESH_MIN_MS' in src:
    raise SystemExit('STOP: throttle already present; no reapply')
if 'if (published == snapshot && Arrays.equals(publishedForward, forward))' not in src:
    raise SystemExit('STOP: original unchanged guard absent')
check = subprocess.run(['git','apply','--check',str(patch)],cwd=root,capture_output=True,text=True)
if check.returncode:
    raise SystemExit('STOP: git apply --check failed: '+check.stderr.strip())
apply = subprocess.run(['git','apply',str(patch)],cwd=root,capture_output=True,text=True)
if apply.returncode:
    raise SystemExit('STOP: git apply failed: '+apply.stderr.strip())
print('E712_APPLIED: SignalController.java only; compilation and device verification NOT RUN')
