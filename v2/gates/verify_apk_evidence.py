#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(msg):
 print("CB6 APK EVIDENCE FAIL:",msg); raise SystemExit(1)
if len(sys.argv)!=2: fail("usage: verify_apk_evidence.py <record>")
p=ROOT/sys.argv[1]
if not p.is_file(): fail("record missing")
d=json.loads(p.read_text(encoding="utf-8"))
required={"schema","feature_id","build_commit","apk_sha256","apk_checks","status"}
if set(d)!=required or d.get("schema")!=1: fail("schema/fields invalid")
if not isinstance(d.get("feature_id"),str) or not d["feature_id"] or d["feature_id"]=="REPLACE_ME": fail("feature identity invalid")
if not re.fullmatch(r"[0-9a-f]{40}",d.get("build_commit","")): fail("build commit invalid")
if not re.fullmatch(r"[0-9a-f]{64}",d.get("apk_sha256","")): fail("APK SHA256 invalid")
if not isinstance(d.get("apk_checks"),list) or not d["apk_checks"] or any(not isinstance(x,str) or not x.strip() for x in d["apk_checks"]): fail("APK checks absent")
if d.get("status")!="VERIFIED": fail("APK evidence not verified")
print("CB6 APK EVIDENCE PASS:",d["feature_id"],d["build_commit"],d["apk_sha256"])
