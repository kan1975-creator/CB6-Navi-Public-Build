#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];cases=[]
def add(name,fn):
 d=json.loads((R/"v2/gates/development_efficiency_rule_candidate_v2.json").read_text());fn(d);cases.append((name,d))
add("drop-introduction-cause",lambda d:d["requirements"].update({"error_introduction_cause_must_be_identified":False}))
add("drop-missed-detection",lambda d:d["requirements"].update({"missed_detection_cause_must_be_identified":False}))
add("allow-insufficient-proposal",lambda d:d["requirements"].update({"insufficient_cause_analysis_blocks_fix_proposal":False}))
add("drop-workflow-dimension",lambda d:d["analysis_dimensions"].remove("actual_workflow_execution_path"))
add("drop-recurrence-evidence",lambda d:d["required_fix_proposal_evidence"].remove("recurrence_prevention"))
add("weaken-existing",lambda d:d["requirements"].update({"broad_read_only_investigation_precedes_device_only_checks":False}))
for name,d in cases:
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);shutil.copytree(R/"v2",t/"v2")
  (t/"v2/gates/development_efficiency_rule_candidate_v2.json").write_text(json.dumps(d,ensure_ascii=False,indent=2))
  cp=subprocess.run(["python3",str(t/"v2/gates/verify_development_efficiency_candidate_v2.py")],cwd=t,capture_output=True,text=True)
  if cp.returncode==0:raise SystemExit("destructive case unexpectedly passed:"+name)
print("CB6 DEVELOPMENT EFFICIENCY V2 CANDIDATE DESTRUCTIVE PASS:",len(cases))
