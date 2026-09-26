#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(m): raise SystemExit("CB6 FINAL ACCEPTANCE FAIL: "+m)
if len(sys.argv)!=2: fail("usage: verify_final_acceptance.py <feature_id>")
fid=sys.argv[1]
feature_path=ROOT/f"v2/gates/features/{fid}.json"
if not feature_path.is_file(): fail("feature gate missing")
f=json.loads(feature_path.read_text())
if f.get("feature_id")!=fid: fail("feature identity mismatch")
apk_path=ROOT/f"v2/gates/apk_evidence/{fid}.json"
dev_path=ROOT/f"v2/gates/device_evidence/{fid}.json"
if not apk_path.is_file(): fail("APK evidence missing")
if not dev_path.is_file(): fail("device evidence missing")
for script,rel,label in [("v2/gates/verify_apk_evidence.py",apk_path.relative_to(ROOT),"APK"),("v2/gates/verify_device_evidence.py",dev_path.relative_to(ROOT),"device")]:
 cp=subprocess.run(["python3",script,str(rel)],cwd=ROOT,text=True,capture_output=True)
 if cp.returncode: fail(label+" verification failed: "+(cp.stdout+cp.stderr).strip())
a=json.loads(apk_path.read_text()); d=json.loads(dev_path.read_text())
if a.get("feature_id")!=fid or d.get("feature_id")!=fid: fail("evidence feature mismatch")
if a.get("build_commit")!=d.get("build_commit") or a.get("apk_sha256")!=d.get("apk_sha256"): fail("APK/device evidence chain mismatch")
if a.get("feature_gate")!=f"v2/gates/features/{fid}.json" or d.get("feature_gate")!=f"v2/gates/features/{fid}.json": fail("evidence does not reference canonical feature gate")
if d.get("apk_evidence")!=f"v2/gates/apk_evidence/{fid}.json": fail("device evidence does not reference canonical APK evidence")
print("CB6 FINAL ACCEPTANCE PASS:",fid)
