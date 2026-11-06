#!/usr/bin/env python3
"""E307: apply E297 candidate to disposable CoMaps tree, STOP on mismatch."""
import hashlib, subprocess, sys
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('usage: apply_307.py COMAPS_ROOT ASSETS_DIR')
root=Path(sys.argv[1]).resolve(); assets=Path(sys.argv[2]).resolve()
java=root/'android/app/src/main/java/app/organicmaps/cb6/signals/VerifiedPackageStager.java'
cpp=root/'android/sdk/src/main/cpp/app/organicmaps/sdk/Cb6AtomicPublish.cpp'
cmake=root/'android/sdk/src/main/cpp/CMakeLists.txt'
assert root.is_dir() and (root/'.git').exists(), 'STOP: missing disposable git tree'
assert java.is_file() and cmake.is_file(), 'STOP: original Java/CMake missing'
assert not cpp.exists(), 'STOP: C++ target collision'
original_blob=subprocess.check_output(['git','hash-object',str(java)],text=True).strip()
assert original_blob=='3e7aefd317f97bd0be95f9fe4fa4340d8d8f02df', 'STOP: Java original blob mismatch'
for name in ('VerifiedPackageStager.java','Cb6AtomicPublish.cpp','CMakeLists.txt.patch'):
 assert (assets/name).is_file(), 'STOP: missing asset '+name
# Check all preconditions before modifying anything.
patch=assets/'CMakeLists.txt.patch'
subprocess.run(['git','-C',str(root),'apply','--check',str(patch)],check=True)
assert cmake.read_text().count('app/organicmaps/sdk/Cb6AtomicPublish.cpp')==0, 'STOP: CMake duplicate SRC'
# Apply the existing E297 source bytes without modification.
cpp.parent.mkdir(parents=True,exist_ok=True)
cpp.write_bytes((assets/'Cb6AtomicPublish.cpp').read_bytes())
java.write_bytes((assets/'VerifiedPackageStager.java').read_bytes())
subprocess.run(['git','-C',str(root),'apply',str(patch)],check=True)
assert 'app/organicmaps/sdk/Cb6AtomicPublish.cpp' in cmake.read_text()
print('E307 isolated source connection PASS; native compile/runtime NOT verified')
