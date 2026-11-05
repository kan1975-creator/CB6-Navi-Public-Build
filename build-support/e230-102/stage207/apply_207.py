#!/usr/bin/env python3
"""Isolated stage207 candidate: apply E185 -> E189 -> E194 to disposable CoMaps tree.
Requires separately approved integration; this script does not invoke Gradle or GitHub.
"""
from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: apply_207.py COMAPS_ROOT STAGE207_ASSET_DIR")
root = Path(sys.argv[1]).resolve()
assets = Path(sys.argv[2]).resolve()
if not root.is_dir() or not (root / 'android/app').is_dir():
    raise SystemExit('STOP: disposable CoMaps tree not found')

def apply(rel):
    patch = assets / rel
    if not patch.is_file():
        raise SystemExit(f'STOP: missing {rel}')
    subprocess.run(['git', '-C', str(root), 'apply', '--check', str(patch)], check=True)
    subprocess.run(['git', '-C', str(root), 'apply', str(patch)], check=True)

# E185: insert new Java files without overwriting any pre-existing original.
for rel in (
    'android/app/src/main/java/app/organicmaps/cb6/signals/Cb6SignalDistributionConfig.java',
    'android/app/src/main/java/app/organicmaps/cb6/signals/Cb6SignalUpdateCoordinator.java',
    'android/app/src/main/java/app/organicmaps/cb6/signals/Cb6VerifiedDownloader.java',
):
    source = assets / rel
    target = root / rel
    if not source.is_file() or target.exists():
        raise SystemExit(f'STOP: missing candidate or target already exists: {rel}')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
for rel in ('patches/Cb6DataStatusFragment.patch', 'patches/MwmActivity.patch', 'patches/build.gradle.patch'):
    apply(rel)
# E189 then E194: must remain sequential.
apply('stage189/after-E185.patch')
apply('stage194/after-E189.patch')
# E257: diagnostic logging only, after E194 changes the Coordinator.
apply('patches/after-E194-Coordinator-diagnostics.patch')
print('E207 isolated patch sequence applied; compile/runtime NOT verified')
