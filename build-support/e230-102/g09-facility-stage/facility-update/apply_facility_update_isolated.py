#!/usr/bin/env python3
"""Run only AFTER existing G09 integrated source and 14,934-row staging.
Never re-run convenience, signal, or symbol overlay installers.
"""
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: apply_facility_update_isolated.py <restored-comaps-root>')
root=Path(sys.argv[1]).resolve()
here=Path(__file__).resolve().parent
required=[
 root/'android/app/src/main/java/app/organicmaps/MwmActivity.java',
 root/'android/app/src/main/java/app/organicmaps/settings/Cb6DataStatusFragment.java',
 root/'android/app/src/main/java/app/organicmaps/cb6/facilities/Cb6FacilityDbDownload.java',
 root/'android/app/src/main/java/app/organicmaps/cb6/facilities/Cb6FacilityDbInstaller.java',
 root/'android/app/src/main/assets/cb6_facilities.sqlite',
]
for p in required:
 if not p.is_file(): raise SystemExit('STOP_REQUIRED_G09_FILE_MISSING: '+str(p))
# Fail before writes if UI or startup anchors differ.
activity=required[0].read_text(); fragment=required[1].read_text()
if activity.count('        app.organicmaps.cb6.facilities.Cb6FacilityDbDownload.downloadConfigured(this);')!=1:
 raise SystemExit('STOP_AUTO_DOWNLOAD_ANCHOR')
if fragment.count('      update.setEnabled(false);\n      update.setSummary("更新先または安全な更新接続が未確定のため利用できません");')!=1:
 raise SystemExit('STOP_UPDATE_UI_ANCHOR')
for script in ('apply_g09_safe_update_source.py','apply_g09_facility_update_ui.py'):
 subprocess.run([sys.executable,str(here/script),str(root)],check=True)
print('G09_UPDATE_ISOLATED_PATCH_APPLIED; URL_CONFIG_NOT_PROVIDED')
