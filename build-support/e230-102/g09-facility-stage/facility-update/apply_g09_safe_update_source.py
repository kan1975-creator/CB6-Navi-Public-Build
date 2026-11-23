#!/usr/bin/env python3
"""Replace only the two G09 Java files and remove startup auto-download, fail closed."""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit('usage: apply_g09_safe_update_source.py <comaps-root>')
root=Path(sys.argv[1]); here=Path(__file__).resolve().parent
pkg=root/'android/app/src/main/java/app/organicmaps/cb6/facilities'
for name in ('Cb6FacilityDbDownload.java','Cb6FacilityDbInstaller.java'):
    dest=pkg/name
    if not dest.is_file(): raise SystemExit('STOP_MISSING_G09_SOURCE_'+name)
    original=(here/name).read_text()
    if 'class '+name.removesuffix('.java') not in dest.read_text(): raise SystemExit('STOP_UNEXPECTED_G09_SOURCE_'+name)
activity=root/'android/app/src/main/java/app/organicmaps/MwmActivity.java'
if not activity.is_file(): raise SystemExit('STOP_MISSING_ACTIVITY')
s=activity.read_text()
anchor='        app.organicmaps.cb6.facilities.Cb6FacilityDbDownload.downloadConfigured(this);'
if s.count(anchor)!=1: raise SystemExit('STOP_AUTO_DOWNLOAD_ANCHOR')
# All preconditions checked before any file write.
for name in ('Cb6FacilityDbDownload.java','Cb6FacilityDbInstaller.java'):
    (pkg/name).write_text((here/name).read_text())
activity.write_text(s.replace(anchor,'        // G09 updates are user-initiated in CB6 offline-data settings.',1))
print('G09_SAFE_UPDATE_SOURCES_APPLIED')
