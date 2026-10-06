#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_remaining_gaps_e2e_independent_review.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("independent baseline failed")
def cf1(d):d["cases"][0]["work_unit"]["change_id"]="CF-01"
def cf2(d):d["cases"][1]["work_unit"]["dimensions"][0]["evidence_refs"][0]["explicit_binding"]=True
def cf3(d):d["cases"][2]["work_unit"]["approval"]["purpose"]="remaining-gap-test"
def cf4(d):d["cases"][3]["work_unit"]["dimensions"][0]["applicability"]="APPLIED"
def cf5(d):d["cases"][4]["work_unit"]["independent_review"]={"accepted":True,"evidence_refs":["IR-1"],"evidence_type":"independent_review"}
def expected(d):d["cases"][0]["expected"]="PASS"
for name,mut in [("identity",cf1),("cross-work-unit",cf2),("approval-binding",cf3),("blocked",cf4),("review",cf5),("expected-tamper",expected)]:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/development_auditor_v2_remaining_gaps_e2e_cases.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("independent destructive case passed:"+name)
  print("PASS expected independent rejection:",name)
print("AUDITOR V2 REMAINING GAPS INDEPENDENT DESTRUCTIVE PASS: 6")
