#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];review=R/"v2/gates/development_efficiency_independent_review.json";candidate=R/"v2/gates/development_efficiency_rule_candidate.json";cases=[]
def add(n,p,fn):d=json.loads(p.read_text());fn(d);cases.append((n,p.name,d))
add("wrong-run",review,lambda d:d["evidence"].__setitem__("candidate_gate_run",0))
add("scope-weakened",candidate,lambda d:d.__setitem__("scope","current_only"))
add("self-active",candidate,lambda d:d.__setitem__("status","ACTIVE"))
add("approval-weakened",candidate,lambda d:d["non_weakening"].remove("OPS-USER-APPROVAL-BEFORE-FIX-001"))
add("review-five-false",review,lambda d:d["checks"].__setitem__("five_requirements_preserved",False))
for k in ("acceptance_criteria_fixed_before_implementation_or_diagnostic_apk","broad_read_only_investigation_precedes_device_only_checks","observation_points_bundled_across_relevant_execution_path_when_practical","actions_wait_allows_non_conflicting_read_only_parallel_work","unnecessary_additional_diagnostics_after_fixed_criteria_pass_forbidden"):
 add("off-"+k,candidate,lambda d,k=k:d["requirements"].__setitem__(k,False))
for name,fn,d in cases:
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);shutil.copytree(R/"v2",t/"v2");(t/"v2/gates"/fn).write_text(json.dumps(d,indent=2))
  p=subprocess.run(["python3",str(t/"v2/gates/verify_development_efficiency_independent_review.py")],cwd=t,capture_output=True,text=True)
  if p.returncode==0:raise SystemExit("destructive case unexpectedly passed: "+name)
print("CB6 DEVELOPMENT EFFICIENCY INDEPENDENT REVIEW DESTRUCTIVE PASS:",len(cases),"weakenings rejected")
