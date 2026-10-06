#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_remaining_gaps_e2e_independent_review.py"];F="v2/gates/development_auditor_v2_remaining_gaps_e2e_cases.json"
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("baseline failed")
def heal(c):
 w=c["work_unit"];i=c["id"]
 if i=="CF-01A":w["change_id"]="CF-01A"
 elif i=="CF-01B":w["target_head"]=w["basis_head"]
 elif i=="CF-02":w["dimensions"][0]["evidence_refs"][0]["explicit_binding"]=True
 elif i.startswith("CF-03"):
  for k in ["change_id","basis_head","purpose","affected_domains","planned_paths","forbidden_scope"]:w["approval"][k]=w.get(k)
 elif i=="CF-04":w["dimensions"][0]["applicability"]="APPLIED"
 else:w["independent_review"]={"accepted":True,"evidence_refs":["IR-1"],"evidence_type":"independent_review"}
ids=["CF-01A","CF-01B","CF-02"]+[f"CF-03{x}" for x in "ABCDEF"]+["CF-04","CF-05A","CF-05B"]
for i in ids:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/F;d=json.loads(p.read_text());heal(next(x for x in d["cases"] if x["id"]==i));p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("defect erasure passed:"+i)
print("AUDITOR V2 REMAINING GAPS INDEPENDENT DESTRUCTIVE PASS: 12")
