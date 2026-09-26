#!/usr/bin/env python3
"""Audit workflow references and record/verify exact generated source identity."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('manifest', type=Path)
p.add_argument('--verify', action='store_true')
a = p.parse_args()
root = a.root.resolve()
tracked = {
 'android/app/build.gradle', 'android/app/src/main/java/app/organicmaps/MwmActivity.java',
 'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp',
 'android/sdk/src/main/java/app/organicmaps/sdk/Framework.java',
 'libs/map/user_mark.hpp', 'libs/map/user_mark.cpp',
}
if a.verify:
    expected = json.loads(a.manifest.read_text())
    for path, sha in expected.items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != sha:
            raise SystemExit('Post-configure source changed: '+path)
    print('PASS configure did not overwrite any Gate 1 source or owned SVG')
else:
    changed = set(subprocess.check_output(['git','-C',str(root),'diff','--name-only'], text=True).splitlines())
    if changed != tracked:
        raise SystemExit('Unexpected changed upstream surfaces: '+repr(changed ^ tracked))
    new = subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard'], text=True).splitlines()
    allowed = (
      'android/app/src/main/java/app/organicmaps/cb6/signals/',
      'android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc',
      'libs/map/cb6_signal_mark.hpp',
      'data/styles/default/light/symbols/cb6-signal-',
      'data/styles/default/dark/symbols/cb6-signal-',
    )
    if any(not x.startswith(allowed) for x in new):
        raise SystemExit('Unexpected untracked upstream surface: '+repr(new))
    hashes = {x: hashlib.sha256((root/x).read_bytes()).hexdigest() for x in sorted(tracked | set(new))}
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(hashes, indent=2)+'\n')
    print('PASS source scope: '+str(len(hashes))+' files, only identity and signals')
