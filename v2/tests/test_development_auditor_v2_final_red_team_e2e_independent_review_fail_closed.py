#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2];CMD=["python3","v2/gates/verify_development_auditor_v2_final_red_team_e2e_independent_review.py"]
def run(r):return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode:raise SystemExit("final-red-team independent baseline failed")
def rt1(d):d["cases"][0]["work_unit"]["risk"]["mandatory_checks_reduced"]=False
def rt2(d):w=d["cases"][1]["work_unit"]["dimensions"][0];w["reason"]="not material";w["applicability_evidence_refs"]=["E-1"]
def rt3(d):d["cases"][2]["work_unit"]["resynchronization"]["resynchronized"]=True
def rt4(d):d["cases"][3]["work_unit"]["method_pipeline"]["completed"].insert(4,"change_impact_before_implementation")
def rt5(d):d["cases"][4]["work_unit"]["outcome"]="STOP"
def exp(d):d["cases"][0]["expected"]="PASS"
for name,mut in [("risk",rt1),("not-applicable",rt2),("resync",rt3),("method",rt4),("outcome",rt5),("expected-tamper",exp)]:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo";shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"));p=r/"v2/gates/development_auditor_v2_final_red_team_e2e_cases.json";d=json.loads(p.read_text());mut(d);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
  if run(r).returncode==0:raise SystemExit("independent destructive case passed:"+name)
  print("PASS expected independent rejection:",name)
print("AUDITOR V2 FINAL RED TEAM INDEPENDENT DESTRUCTIVE PASS: 6")
