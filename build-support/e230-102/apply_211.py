#!/usr/bin/env python3
"""Stage 221: apply ONLY seven stage-211 files and one SignalController line, fail closed."""
from pathlib import Path
import sys, zipfile, hashlib

if len(sys.argv)!=3:
    raise SystemExit('usage: apply_211.py CANDIDATE_211.zip COMAPS_ROOT')
archive=Path(sys.argv[1]); root=Path(sys.argv[2]);
if not archive.is_file() or not root.is_dir():
    raise SystemExit('STOP: required input absent')
with zipfile.ZipFile(archive) as z:
    entries=[n for n in z.namelist() if n.startswith('android/') and (n.endswith('.java') or n.endswith('.xml'))]
    if len(entries)!=7:
        raise SystemExit('STOP: expected exactly seven Java/XML files')
    target=root/'android/app/src/main/java/app/organicmaps/cb6/signals/SignalController.java'
    before='new CompositeSignalProvider(new OverpassSignalProvider(), new VerifiedSignalProvider())'
    after='new CompositeSignalProvider(new OverpassSignalProvider(this.context), new VerifiedSignalProvider())'
    content=target.read_text(encoding='utf-8')
    if content.count(before)!=1 or after in content:
        raise SystemExit('STOP: overlay136 SignalController anchor missing/non-unique')
    # Validate all targets before any write, avoid path traversal and unexpected replacements.
    staged=[]
    for name in entries:
        rel=Path(name)
        if '..' in rel.parts or rel.is_absolute():
            raise SystemExit('STOP: unsafe archive path')
        dest=root/rel
        if not dest.parent.is_dir():
            raise SystemExit('STOP: expected target directory absent: '+str(dest.parent))
        data=z.read(name)
        staged.append((dest,data))
    # Only after all checks pass, write to disposable CoMaps workspace.
    for dest,data in staged:
        dest.write_bytes(data)
    target.write_text(content.replace(before,after,1),encoding='utf-8')
    print('PASS: 7 files and one-line SignalController edit applied to disposable workspace')
