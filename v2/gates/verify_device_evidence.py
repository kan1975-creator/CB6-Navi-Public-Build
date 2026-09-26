#!/usr/bin/env python3
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(msg):
 print("CB6 DEVICE EVIDENCE FAIL:",msg); raise SystemExit(1)
if len(sys.argv)!=2: fail("usage: verify_device_evidence.py <record>")
p=ROOT/sys.argv[1]
if not p.is_file(): fail("record missing")
d=json.loads(p.read_text(encoding="utf-8"))
required={"schema","feature_id","build_commit","apk_evidence","apk_sha256","device","android_version","checks","status"}
if set(d)!=required or d.get("schema")!=1: fail("schema/fields invalid")
if not isinstance(d.get("feature_id"),str) or not d["feature_id"] or d["feature_id"]=="REPLACE_ME": fail("feature identity invalid")
if not re.fullmatch(r"[0-9a-f]{40}",d.get("build_commit","")): fail("build commit invalid")
if not re.fullmatch(r"[0-9a-f]{64}",d.get("apk_sha256","")): fail("APK SHA256 invalid")
apk_rel=d.get("apk_evidence","")
apk_path=ROOT/apk_rel
if not apk_path.is_file(): fail("APK evidence missing")
apk=json.loads(apk_path.read_text(encoding="utf-8"))
if apk.get("status")!="VERIFIED": fail("referenced APK evidence not verified")
if apk.get("feature_id")!=d["feature_id"] or apk.get("build_commit")!=d["build_commit"] or apk.get("apk_sha256")!=d["apk_sha256"]: fail("device evidence does not match APK evidence")
cp=subprocess.run(["python3","v2/gates/verify_apk_evidence.py",apk_rel],cwd=ROOT,text=True,capture_output=True)
if cp.returncode!=0: fail("referenced APK evidence fails verification")
checks=d.get("checks")
if not isinstance(checks,list) or not checks: fail("device checks absent")
for x in checks:
 if set(x)!={"id","result","evidence"} or not x.get("id") or x.get("result")!="PASS" or not x.get("evidence"): fail("device check not accepted")
if d.get("device")!="CB6" or str(d.get("android_version"))!="13": fail("device identity mismatch")
if d.get("status")!="ACCEPTED": fail("device evidence not accepted")
print("CB6 DEVICE EVIDENCE PASS:",d["feature_id"],d["build_commit"],d["apk_sha256"])
