#!/usr/bin/env python3
import json,re,sys,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(msg):
 print("CB6 APK EVIDENCE FAIL:",msg); raise SystemExit(1)
if len(sys.argv)!=2: fail("usage: verify_apk_evidence.py <record>")
p=ROOT/sys.argv[1]
if not p.is_file(): fail("record missing")
d=json.loads(p.read_text(encoding="utf-8"))
required={"schema","feature_id","build_commit","feature_gate","apk_path","apk_sha256","apk_checks","status"}
if set(d)!=required or d.get("schema")!=1: fail("schema/fields invalid")
if not isinstance(d.get("feature_id"),str) or not d["feature_id"] or d["feature_id"]=="REPLACE_ME": fail("feature identity invalid")
if not re.fullmatch(r"[0-9a-f]{40}",d.get("build_commit","")): fail("build commit invalid")
cp=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True)
if cp.returncode!=0: fail("cannot resolve repository HEAD")
if d["build_commit"]!=cp.stdout.strip(): fail("build commit does not match repository HEAD")
if not re.fullmatch(r"[0-9a-f]{64}",d.get("apk_sha256","")): fail("APK SHA256 invalid")
apk=ROOT/d.get("apk_path","")
if not apk.is_file() or apk.suffix.lower()!=".apk": fail("APK artifact missing")
actual=hashlib.sha256(apk.read_bytes()).hexdigest()
if actual!=d["apk_sha256"]: fail("APK SHA256 does not match artifact")
feature_path=ROOT/d.get("feature_gate","")
if not feature_path.is_file(): fail("feature gate missing")
feature=json.loads(feature_path.read_text(encoding="utf-8"))
if feature.get("feature_id")!=d["feature_id"]: fail("APK evidence feature gate identity mismatch")
planned=feature.get("apk_checks")
if not isinstance(planned,list) or not planned or any(not isinstance(x,dict) or set(x)!={"id","description"} for x in planned): fail("feature APK check plan invalid")
planned_ids=[x.get("id") for x in planned]
if any(not x for x in planned_ids) or len(set(planned_ids))!=len(planned_ids): fail("feature APK check ids invalid")
checks=d.get("apk_checks")
if not isinstance(checks,list) or not checks: fail("APK checks absent")
for x in checks:
 if not isinstance(x,dict) or set(x)!={"id","result","evidence"} or not x.get("id") or x.get("result")!="PASS" or not x.get("evidence"): fail("APK check not verified")
actual_ids=[x["id"] for x in checks]
if len(set(actual_ids))!=len(actual_ids): fail("APK evidence check ids duplicated")
if set(actual_ids)!=set(planned_ids): fail("APK evidence does not cover planned checks")
if d.get("status")!="VERIFIED": fail("APK evidence not verified")
print("CB6 APK EVIDENCE PASS:",d["feature_id"],d["build_commit"],d["apk_sha256"])
