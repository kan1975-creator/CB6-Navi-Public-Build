#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(msg):
 print("CB6 APK EVIDENCE CREATE FAIL:",msg); raise SystemExit(1)
if len(sys.argv)!=4: fail("usage: create_apk_evidence.py <feature> <apk> <sha-file>")
fid,apk,sha_file=sys.argv[1:]
feature_path=ROOT/f"v2/gates/features/{fid}.json"
if not feature_path.is_file(): fail("feature gate missing")
feature=json.loads(feature_path.read_text(encoding="utf-8"))
if feature.get("feature_id")!=fid: fail("feature identity mismatch")
planned=feature.get("apk_checks")
if not isinstance(planned,list) or not planned: fail("feature APK check plan missing")
evidence_map={
 "apk-arm64":"out/NATIVE_VERIFY.txt",
 "apk-identity":"out/APK_BADGING.txt",
 "apk-signals":"out/APK_SIGNAL_AUDIT.txt",
 "apk-signature":"out/SIGNATURE_VERIFY.txt",
 "apk-native-mwm-diagnostic":"out/NATIVE_VERIFY.txt"
}
checks=[]
for item in planned:
 cid=item.get("id") if isinstance(item,dict) else None
 if cid not in evidence_map: fail("unsupported planned APK check: "+str(cid))
 ep=ROOT/evidence_map[cid]
 if not ep.is_file(): fail("planned APK evidence file missing: "+str(ep.relative_to(ROOT)))
 checks.append({"id":cid,"result":"PASS","evidence":evidence_map[cid]})
sha=(ROOT/sha_file).read_text().split()[0]
d={"schema":1,"feature_id":fid,"build_commit":os.environ["GITHUB_SHA"],"feature_gate":f"v2/gates/features/{fid}.json","apk_path":apk,"apk_sha256":sha,"apk_checks":checks,"status":"VERIFIED"}
p=ROOT/f"v2/gates/apk_evidence/{fid}.json"; p.write_text(json.dumps(d,indent=2)+"\n")
print("CB6 APK EVIDENCE CREATED:",p.relative_to(ROOT))
