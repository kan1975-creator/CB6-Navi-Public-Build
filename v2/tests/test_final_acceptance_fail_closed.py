#!/usr/bin/env python3
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns("out","comaps"))
 head=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,capture_output=True,check=True).stdout.strip()
 fid="accepttest"; feature_rel=f"v2/gates/features/{fid}.json"; apk_rel=f"v2/gates/apk_evidence/{fid}.json"; dev_rel=f"v2/gates/device_evidence/{fid}.json"
 (root/feature_rel).write_text(json.dumps({"feature_id":fid,"apk_checks":[{"id":"apk","description":"apk"}],"device_checks":[{"id":"device","description":"device"}]}))
 apk=root/"out/final.apk"; apk.parent.mkdir(exist_ok=True); apk.write_bytes(b"final-acceptance"); sha=hashlib.sha256(apk.read_bytes()).hexdigest()
 (root/apk_rel).write_text(json.dumps({"schema":1,"feature_id":fid,"build_commit":head,"feature_gate":feature_rel,"apk_path":"out/final.apk","apk_sha256":sha,"apk_checks":[{"id":"apk","result":"PASS","evidence":"verified"}],"status":"VERIFIED"}))
 (root/dev_rel).write_text(json.dumps({"schema":1,"feature_id":fid,"build_commit":head,"feature_gate":feature_rel,"apk_evidence":apk_rel,"apk_sha256":sha,"device":"CB6","android_version":"13","checks":[{"id":"device","result":"PASS","evidence":"observed"}],"status":"ACCEPTED"}))
 ok=subprocess.run(["python3","v2/gates/verify_final_acceptance.py",fid],cwd=root,text=True,capture_output=True)
 if ok.returncode: raise SystemExit("FINAL ACCEPTANCE TEST FAIL baseline: "+ok.stdout+ok.stderr)
 d=json.loads((root/dev_rel).read_text()); d["apk_evidence"]="v2/gates/apk_evidence/other.json"; (root/dev_rel).write_text(json.dumps(d))
 bad=subprocess.run(["python3","v2/gates/verify_final_acceptance.py",fid],cwd=root,text=True,capture_output=True); out=bad.stdout+bad.stderr
 if bad.returncode==0 or "device verification failed" not in out: raise SystemExit("FINAL ACCEPTANCE TEST FAIL broken-chain: "+out)
 print("PASS final acceptance rejects broken evidence chain")
