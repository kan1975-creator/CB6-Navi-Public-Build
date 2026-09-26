#!/usr/bin/env python3
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]

def run_case(name,mutate,needle):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns("out","comaps"))
  head=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,capture_output=True,check=True).stdout.strip()
  apk_file=root/"out/test.apk"; apk_file.parent.mkdir(exist_ok=True); apk_file.write_bytes(b"cb6-device-test-apk")
  sha=hashlib.sha256(apk_file.read_bytes()).hexdigest()
  apk_rel="v2/gates/apk_evidence/device-test.json"
  apk_path=root/apk_rel
  apk={"schema":1,"feature_id":"testfeature","build_commit":head,"apk_path":"out/test.apk","apk_sha256":sha,"apk_checks":["manifest/resources verified"],"status":"VERIFIED"}
  apk_path.write_text(json.dumps(apk))
  feature_rel="v2/gates/features/device-test.json"
  feature_path=root/feature_rel
  feature={"feature_id":"testfeature","device_checks":[{"id":"signal-render","description":"signal renders on CB6"}]}
  feature_path.write_text(json.dumps(feature))
  dev_rel="v2/gates/device_evidence/device-test.json"
  dev_path=root/dev_rel
  dev={"schema":1,"feature_id":"testfeature","build_commit":head,"feature_gate":feature_rel,"apk_evidence":apk_rel,"apk_sha256":sha,"device":"CB6","android_version":"13","checks":[{"id":"signal-render","result":"PASS","evidence":"observed on CB6"}],"status":"ACCEPTED"}
  mutate(dev,apk); apk_path.write_text(json.dumps(apk)); dev_path.write_text(json.dumps(dev))
  cp=subprocess.run(["python3","v2/gates/verify_device_evidence.py",dev_rel],cwd=root,text=True,capture_output=True)
  out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(f"DEVICE EVIDENCE TEST FAIL {name}: rc={cp.returncode}\n{out}")
  print("PASS expected device evidence rejection:",name,"->",needle)

cases=[
 ("apk-not-verified",lambda d,a:a.__setitem__("status","PENDING"),"referenced APK evidence not verified"),
 ("apk-sha-mismatch",lambda d,a:d.__setitem__("apk_sha256","b"*64),"device evidence does not match APK evidence"),
 ("build-commit-mismatch",lambda d,a:d.__setitem__("build_commit","a"*40),"device evidence does not match APK evidence"),
 ("pending-check",lambda d,a:d["checks"][0].__setitem__("result","PENDING"),"device check not accepted"),
 ("status-pending",lambda d,a:d.__setitem__("status","PENDING"),"device evidence not accepted"),
 ("missing-planned-check",lambda d,a:d.__setitem__("checks",[]),"device checks absent"),
 ("extra-check",lambda d,a:d["checks"].append({"id":"unplanned","result":"PASS","evidence":"extra"}),"device evidence does not cover planned checks"),
 ("duplicate-check",lambda d,a:d["checks"].append(dict(d["checks"][0])),"device evidence check ids duplicated"),
]
for case in cases: run_case(*case)
print("PASS device evidence destructive cases rejected")
