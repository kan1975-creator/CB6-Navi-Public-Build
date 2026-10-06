#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_atomic_coverage_e2e.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("atomic baseline failed")
F=json.loads((S/"v2/gates/development_auditor_v2_atomic_coverage_e2e_cases.json").read_text())
targets=[]
for kind in ("contract","schema","method"):
 d=json.loads((S/F["authorities"][kind]).read_text())
 for sec in F[kind+"_sections"]:
  v=d[sec]
  if isinstance(v,dict):
   for k in v:targets.append((kind,sec,k))
  elif isinstance(v,list):
   for i in range(len(v)):targets.append((kind,sec,i))
  else:targets.append((kind,sec,None))
def mutate(d,sec,key):
 if key is None:d[sec]="__BROKEN__"
 elif isinstance(key,int):d[sec][key]="__BROKEN__"
 else:
  v=d[sec][key]
  if isinstance(v,bool):d[sec][key]=not v
  elif isinstance(v,list):d[sec][key]=v[:-1] if v else ["__BROKEN__"]
  elif isinstance(v,dict):d[sec][key]={}
  else:d[sec][key]="__BROKEN__"
for kind,sec,key in targets:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/F["authorities"][kind];d=json.loads(p.read_text());mutate(d,sec,key);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit(f"atomic authority mutation passed:{kind}:{sec}:{key}")
# Explicitly prove the two N/A defects independently and every Method stage omission.
for defect in ("reason","applicability_evidence_refs"):
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/development_auditor_work_unit_schema_v1.json";d=json.loads(p.read_text());d["not_applicable_required"].remove(defect);p.write_text(json.dumps(d,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("N/A independent defect passed:"+defect)
for stage in json.loads((S/F["authorities"]["method"]).read_text())["feature_development_pipeline"]:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/F["authorities"]["method"];d=json.loads(p.read_text());d["feature_development_pipeline"].remove(stage);p.write_text(json.dumps(d,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("method stage omission passed:"+stage)
print("AUDITOR V2 ATOMIC COVERAGE DESTRUCTIVE PASS:",len(targets)+2+11,"atomic mutations")
