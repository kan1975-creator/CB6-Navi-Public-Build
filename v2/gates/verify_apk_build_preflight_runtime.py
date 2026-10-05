#!/usr/bin/env python3
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REQS=[
"latest_authority_checked","pinned_upstream_revalidated","feature_gate_passed",
"impact_and_research_records_present","generated_source_integration_checked",
"change_allowlist_checked","frozen_assets_checked","cross_feature_integration_checked",
"routing_search_favorites_offline_non_regression_checked",
"diagnostic_path_checked_when_present","audits_and_destructive_tests_passed",
"diff_check_passed","method_registry_coverage_checked",
"temporary_diagnostic_separated_from_production"]

def run(cmd,cwd=ROOT):
 return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)

def validate_state(state):
 missing=[k for k in REQS if state.get(k) is not True]
 if missing: raise ValueError("preflight requirements failed: "+", ".join(missing))

def txt(path):
 return path.read_text(encoding="utf-8",errors="ignore") if path.exists() else ""

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--feature",required=True,choices=["signals","convenience-brands","convenience-mwm-diagnostic"])
 ap.add_argument("--tree",default="comaps")
 ap.add_argument("--mode",required=True,choices=["production","production-diagnostic","diagnostic"])
 a=ap.parse_args()
 tree=(ROOT/a.tree).resolve(); state={k:False for k in REQS}; errors=[]
 def check(k,ok,msg):
  state[k]=bool(ok)
  if not ok: errors.append(k+": "+msg)

 contract=json.loads((ROOT/"v2/gates/apk_build_preflight_candidate.json").read_text())
 active=run(["python3","v2/gates/verify_apk_build_preflight_active.py"])
 repo_head=run(["git","rev-parse","HEAD"]).stdout.strip()
 gh=os.environ.get("GITHUB_SHA","")
 check("latest_authority_checked",contract.get("status")=="ACTIVE" and contract.get("fail_closed") is True and (not gh or gh==repo_head),"ACTIVE authority/GITHUB_SHA mismatch")

 method=json.loads((ROOT/"v2/gates/development_method_contract.json").read_text())
 pinned=method["pinned_upstream_source_policy"]["commit"]
 up=run(["git","rev-parse","HEAD"],cwd=tree)
 check("pinned_upstream_revalidated",up.returncode==0 and up.stdout.strip()==pinned,"generated tree is not pinned CoMaps")

 gate=run(["python3","v2/gates/verify_project_gate.py","--require-feature-build","--feature="+a.feature])
 check("feature_gate_passed",gate.returncode==0,"feature gate rejected build")

 fp=ROOT/f"v2/gates/features/{a.feature}.json"
 feature=json.loads(fp.read_text()) if fp.exists() else {}
 ip=ROOT/feature.get("impact_record","")
 rp=ROOT/feature.get("research_record","")
 impact=json.loads(ip.read_text()) if ip.is_file() else {}
 research=json.loads(rp.read_text()) if rp.is_file() else {}
 records=(feature.get("impact_checked") is True and impact.get("feature_id")==a.feature and
          research.get("feature_id")==a.feature and research.get("status")=="COMPLETE" and
          research.get("completed_before_implementation") is True)
 check("impact_and_research_records_present",records,"impact/research evidence incomplete")

 diff=run(["git","diff","--name-only"],cwd=tree)
 paths=[x.strip() for x in diff.stdout.splitlines() if x.strip()]
 mwm=txt(tree/"android/app/src/main/java/app/organicmaps/MwmActivity.java")
 fw=txt(tree/"android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp")
 sigjni=txt(tree/"android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc")
 sig=("nativeSetCb6Signals" in sigjni and '#include "cb6_signal_jni.inc"' in fw and "mCb6Signals" in mwm)
 conv=("nativeCb6CollectConvenienceMarks" in fw and "nativeSetCb6ConvenienceMarks" in fw)
 diag=("nativeCb6ConvenienceDiagnostic" in fw or "CB6-CONVENIENCE-ZOOM-DIAG" in mwm)
 generated=bool(paths)
 if a.feature=="signals": generated=generated and sig
 elif a.feature=="convenience-brands": generated=generated and sig and conv
 else: generated=generated and ("nativeCb6ConvenienceDiagnostic" in fw)
 check("generated_source_integration_checked",generated,"expected generated integration missing")

 allowed_prefixes=("android/","libs/map/","libs/storage/","data/styles/default/")
 allowed_exact={"libs/platform/http_request.cpp","data/styles/vehicle/include/Icons.mapcss"}
 generated_priority_suffix="/include/priorities_4_overlays.prio.txt"
 def allowed_path(p):
  return p.startswith(allowed_prefixes) or p in allowed_exact or (p.startswith("data/styles/") and p.endswith(generated_priority_suffix))
 escaped=[p for p in paths if not allowed_path(p)]
 allow=bool(paths) and not escaped
 check("change_allowlist_checked",allow,"generated diff escaped approved integration surfaces: "+",".join(escaped))

 densities={"mdpi":22,"hdpi":32,"xhdpi":43,"6plus":52,"xxhdpi":65,"xxxhdpi":77}
 brands=("cb6-seven","cb6-familymart","cb6-lawson","cb6-seicomart","cb6-ministop","cb6-mybasket")
 assets=True
 if a.feature=="convenience-brands":
  try:
   from PIL import Image
   for theme in ("light","dark"):
    for density,size in densities.items():
     for brand in brands:
      p=tree/f"data/styles/default/{theme}/{density}/{brand}.png"
      with Image.open(p) as im:
       if max(im.size)!=size: assets=False
  except Exception: assets=False
 else:
  assets=not any(any(b in p for b in brands) for p in paths)
 check("frozen_assets_checked",assets,"frozen convenience asset boundary changed")

 cross=(sig and not conv) if a.feature=="signals" else ((sig and conv) if a.feature=="convenience-brands" else (not sig and not conv and "nativeCb6ConvenienceDiagnostic" in fw))
 check("cross_feature_integration_checked",cross,"Signal/Convenience composition does not match build type")

 protected=("libs/routing/","libs/search/","android/app/src/main/java/app/organicmaps/search/",
            "android/app/src/main/java/app/organicmaps/bookmarks/","android/app/src/main/java/app/organicmaps/downloader/")
 nonreg=not any(p.startswith(protected) for p in paths)
 check("routing_search_favorites_offline_non_regression_checked",nonreg,"protected routing/search/favorites/offline path changed")

 diag_ok=(not diag) if a.mode=="production" else diag
 check("diagnostic_path_checked_when_present",diag_ok,"diagnostic execution path does not match declared mode")

 audits=True
 if a.feature=="signals":
  cmds=[["python3","v2/audits/audit_identity.py",str(tree)],["python3","v2/audits/audit_signals.py",str(tree)],["python3","v2/tests/signals_audit_selftest.py",str(tree)]]
 elif a.feature=="convenience-brands":
  cmds=[["python3","v2/audits/audit_identity.py",str(tree)],["python3","v2/audits/audit_signals.py",str(tree),"--allow-convenience-style"],["python3","v2/tests/signals_audit_selftest.py",str(tree),"--allow-convenience-style"],["python3","v2/audits/audit_convenience.py"],["python3","v2/tests/convenience_audit_selftest.py"]]
 else:
  cmds=[["python3","v2/audits/audit_identity.py",str(tree)],["python3","v2/audits/audit_convenience.py"],["python3","v2/tests/convenience_audit_selftest.py"]]
 for cmd in cmds:
  if run(cmd).returncode!=0: audits=False
 check("audits_and_destructive_tests_passed",audits,"required audit/destructive proof failed")

 dc=run(["git","diff","--check"],cwd=tree)
 check("diff_check_passed",dc.returncode==0,"git diff --check failed")

 gov=(active.returncode==0 and run(["python3","v2/gates/verify_method_freeze.py"]).returncode==0 and
      run(["python3","v2/gates/verify_operational_rule_registry.py"]).returncode==0 and
      run(["python3","v2/gates/verify_rule_coverage.py"]).returncode==0)
 check("method_registry_coverage_checked",gov,"method/registry/coverage authority failed")

 separated=(a.mode=="production" and not diag) or (a.mode=="diagnostic" and a.feature=="convenience-mwm-diagnostic" and not sig and not conv) or (a.mode=="production-diagnostic" and a.feature=="convenience-brands" and sig and conv and diag)
 check("temporary_diagnostic_separated_from_production",separated,"temporary diagnostic/production classification mismatch")

 try: validate_state(state)
 except ValueError:
  print("CB6 EXECUTABLE APK BUILD PREFLIGHT FAIL:")
  for e in errors: print(" -",e)
  print(json.dumps(state,sort_keys=True))
  raise SystemExit(1)
 print("CB6 EXECUTABLE APK BUILD PREFLIGHT PASS:",a.feature,a.mode)
 print(json.dumps(state,sort_keys=True))

if __name__=="__main__": main()
