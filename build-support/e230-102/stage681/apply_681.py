#!/usr/bin/env python3
"""E681: fail closed when stage307 G1 source differs; no retries or fallback."""
import hashlib, subprocess, sys
from pathlib import Path
if len(sys.argv) != 3:
    raise SystemExit('usage: apply_681.py COMAPS_ROOT PATCH_PATH')
root = Path(sys.argv[1]).resolve()
patch = Path(sys.argv[2]).resolve()
expected = {
    'android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc': ('c12a4b0a1a62555b7a9d350e4a62101ad5aa4f6f87b1e5fab0722ff8f4ee9de4','e10396c444844c191462f2f4efd1067785f38f821ecc4ae70cb1b73cef804c17'),
    'libs/map/cb6_signal_mark.hpp': ('0ef33b34179b207b253b581457ad6d995664c411ec122c9c97c9b0158589199d','6321a3a36cd613652d64a35244da2b5dd6d3f6b86b749eb9273922726047f783'),
}
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
if not (root/'.git').exists(): raise SystemExit('STOP: missing disposable CoMaps git tree')
if digest(patch) != '407aaceb2746f00b53668014b963a546837f7fac9ad7a234d86958d996d092ca':
    raise SystemExit('STOP: patch SHA mismatch')
for relative, (before, after) in expected.items():
    if not (root/relative).is_file() or digest(root/relative) != before:
        raise SystemExit('STOP: stage307 baseline mismatch: '+relative)
subprocess.run(['git','-C',str(root),'apply','--check',str(patch)],check=True)
subprocess.run(['git','-C',str(root),'apply',str(patch)],check=True)
for relative, (before, after) in expected.items():
    if digest(root/relative) != after: raise SystemExit('STOP: post-apply mismatch: '+relative)
print('E681 signal patch connected PASS; native compile/runtime/500m threshold NOT verified')
