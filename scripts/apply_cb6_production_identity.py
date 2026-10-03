#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve()
p=ROOT/'android/app/build.gradle'
s=p.read_text(encoding='utf-8')
old="project.ext.appId = 'app.comaps'";new="project.ext.appId = 'jp.cb6.navi'"
if old in s:s=s.replace(old,new,1)
elif new not in s:raise SystemExit('CB6 production identity: appId anchor missing')
s=s.replace("    ndk.debugSymbolLevel = 'full'\n", "    // CB6 production: packaged native library must be stripped.\n", 1)
s=s.replace("      android.packagingOptions.jniLibs.keepDebugSymbols += '**/liborganicmaps.so'\n", "")
if 'keepDebugSymbols' in s and 'liborganicmaps.so' in s:raise SystemExit('CB6 production identity: native keepDebugSymbols rule remains')
p.write_text(s,encoding='utf-8')
repo=Path(__file__).resolve().parent.parent
subprocess.run([sys.executable,str(repo/'scripts/apply_cb6_production_cleanup.py'),str(ROOT)],check=True)
subprocess.run([sys.executable,str(repo/'CB6_PRODUCTION_AUDIT.py'),str(ROOT)],check=True)
subprocess.run([sys.executable,str(repo/'CB6_FINAL_STATIC_AUDIT.py'),str(ROOT)],check=True)
# configure.sh generates symbols.sdf. The workflow reapplies this script after
# configure, so generated atlas validation becomes mandatory at that point.
if any(ROOT.glob('**/symbols.sdf')):
    subprocess.run([sys.executable,str(repo/'CB6_SYMBOL_ATLAS_AUDIT.py'),str(ROOT)],check=True)
print('CB6 production identity applied: cleanup + production + final static audits enforced; atlas audited when generated')
