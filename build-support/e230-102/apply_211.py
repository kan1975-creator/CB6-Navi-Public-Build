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
    new_data_dir=root/'android/app/src/main/java/app/organicmaps/cb6/data'
    cb6_dir=new_data_dir.parent
    allowed_data_files={
        'Cb6DataStatusRepository.java',
        'Cb6FacilityStatusContract.java',
        'Cb6OverpassDiagnostics.java',
    }
    needs_data_dir=False
    overpass_rel=Path('android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java')
    expected_existing_sha256='cff09b6b2ece75440a5d23500c79e67572d71bdea2a4bed1ba83728b945cd502'
    expected_candidate_sha256='f3c87bf4feef8c3088799c3d00df11c76fa0a51349fd487ed9a1d3ed2c3c5dd9'
    prefs_rel=Path('android/app/src/main/res/xml/prefs_data_management.xml')
    prefs_existing_sha256='2b66299c32112c611086b27193638bee2940ddc507e007f43331662426800646'
    prefs_candidate_sha256='bcc60cf5fa671396a3115efcdefad21a777fb4ff17865912aa5f40c58f01ae09'
    for name in entries:
        rel=Path(name)
        if '..' in rel.parts or rel.is_absolute():
            raise SystemExit('STOP: unsafe archive path')
        dest=root/rel
        if not dest.parent.is_dir():
            if (dest.parent != new_data_dir
                    or dest.name not in allowed_data_files
                    or not cb6_dir.is_dir()
                    or cb6_dir.is_symlink()
                    or new_data_dir.is_symlink()
                    or new_data_dir.exists()):
                raise SystemExit('STOP: expected target directory absent: '+str(dest.parent))
            needs_data_dir=True
        data=z.read(name)
        if rel == overpass_rel:
            if dest.is_symlink() or not dest.is_file():
                raise SystemExit('STOP: expected existing Overpass file absent or unsafe: '+str(dest))
            if hashlib.sha256(dest.read_bytes()).hexdigest()!=expected_existing_sha256:
                raise SystemExit('STOP: existing Overpass SHA-256 mismatch')
            if hashlib.sha256(data).hexdigest()!=expected_candidate_sha256:
                raise SystemExit('STOP: candidate Overpass SHA-256 mismatch')
        elif rel == prefs_rel:
            if dest.is_symlink() or not dest.is_file():
                raise SystemExit('STOP: expected existing prefs XML absent or unsafe: '+str(dest))
            if hashlib.sha256(dest.read_bytes()).hexdigest()!=prefs_existing_sha256:
                raise SystemExit('STOP: existing prefs XML SHA-256 mismatch')
            if hashlib.sha256(data).hexdigest()!=prefs_candidate_sha256:
                raise SystemExit('STOP: candidate prefs XML SHA-256 mismatch')
        elif dest.exists() or dest.is_symlink():
            raise SystemExit('STOP: target already exists: '+str(dest))
        staged.append((dest,data))
    # Preserve the XML-instantiated CB6 status Fragment in R8 release builds.
    rules=root/'android/app/proguard-rules.pro'
    keep_rule='-keep class app.organicmaps.settings.Cb6DataStatusFragment { *; }'
    if rules.is_symlink() or not rules.is_file():
        raise SystemExit('STOP: expected regular ProGuard rules file absent or unsafe')
    rules_content=rules.read_text(encoding='utf-8')
    if keep_rule in rules_content:
        raise SystemExit('STOP: CB6 Fragment keep rule already present')
    if 'Cb6DataStatusFragment' in rules_content:
        raise SystemExit('STOP: unexpected existing CB6 Fragment rule')
    rules_updated=rules_content.rstrip('\n')+'\n'+keep_rule+'\n'
    # Only after all checks pass, write to disposable CoMaps workspace.
    if needs_data_dir:
        new_data_dir.mkdir()
    for dest,data in staged:
        dest.write_bytes(data)
    target.write_text(content.replace(before,after,1),encoding='utf-8')
    rules.write_text(rules_updated,encoding='utf-8')
    print('PASS: 7 files and one-line SignalController edit applied to disposable workspace')
