#!/usr/bin/env python3
import json,shutil,subprocess,tempfile,hashlib
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]

def run_case(name,mutate,needle):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns("out","comaps"))
  rec=root/"v2/gates/apk_evidence/test.json"
  head=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,capture_output=True,check=True).stdout.strip()
  apk=root/"out/test.apk"; apk.parent.mkdir(exist_ok=True); apk.write_bytes(b"cb6-test-apk")
  apk_sha=hashlib.sha256(apk.read_bytes()).hexdigest()
  feature_rel="v2/gates/features/apk-test.json"
  feature=root/feature_rel; feature.write_text(json.dumps({"feature_id":"testfeature","apk_checks":[{"id":"apk-integrity","description":"verify APK integrity"}]}))
  d={"schema":1,"feature_id":"testfeature","build_commit":head,"feature_gate":feature_rel,"apk_path":"out/test.apk","apk_sha256":apk_sha,"apk_checks":[{"id":"apk-integrity","result":"PASS","evidence":"manifest/resources verified"}],"status":"VERIFIED"}
  mutate(d); rec.write_text(json.dumps(d))
  cp=subprocess.run(["python3","v2/gates/verify_apk_evidence.py","v2/gates/apk_evidence/test.json"],cwd=root,text=True,capture_output=True)
  out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(f"APK EVIDENCE TEST FAIL {name}: rc={cp.returncode}\n{out}")
  print("PASS expected APK evidence rejection:",name,"->",needle)

cases=[
 ("pending",lambda d:d.__setitem__("status","PENDING"),"APK evidence not verified"),
 ("bad-build-commit",lambda d:d.__setitem__("build_commit","not-a-commit"),"build commit invalid"),
 ("wrong-build-commit",lambda d:d.__setitem__("build_commit","a"*40),"build commit does not match repository HEAD"),
 ("bad-apk-sha",lambda d:d.__setitem__("apk_sha256","1234"),"APK SHA256 invalid"),
 ("wrong-apk-sha",lambda d:d.__setitem__("apk_sha256","b"*64),"APK SHA256 does not match artifact"),
 ("missing-apk",lambda d:d.__setitem__("apk_path","out/missing.apk"),"APK artifact missing"),
 ("empty-checks",lambda d:d.__setitem__("apk_checks",[]),"APK checks absent"),
 ("pending-check",lambda d:d["apk_checks"][0].__setitem__("result","PENDING"),"APK check not verified"),
 ("extra-check",lambda d:d["apk_checks"].append({"id":"unplanned","result":"PASS","evidence":"extra"}),"APK evidence does not cover planned checks"),
 ("duplicate-check",lambda d:d["apk_checks"].append(dict(d["apk_checks"][0])),"APK evidence check ids duplicated"),
]
for case in cases: run_case(*case)
print("PASS APK evidence destructive cases rejected")
