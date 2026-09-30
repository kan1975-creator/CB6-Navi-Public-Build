#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
C=json.loads((R/"v2/gates/user_approval_before_fix_contract.json").read_text())
def check(d):
 e=[]
 a=d.get("approval")
 if not a: return ["missing approval"]
 for k in C["approval_record"]["required_fields"]:
  if not a.get(k): e.append("missing approval field: "+k)
 if a.get("proposed_change_id")!=d.get("proposed_change_id"): e.append("approval binding mismatch")
 if not a.get("github_reference"): e.append("missing github approval reference")
 if a.get("approved_at","")>=d.get("implementation_started_at",""): e.append("approval is not pre-implementation")
 return e
if __name__=="__main__":
 p=Path(sys.argv[1]) if len(sys.argv)>1 else None
 if not p: raise SystemExit("usage: verify_user_approval_before_fix.py evidence.json")
 e=check(json.loads(p.read_text()))
 if e:
  print("CB6 PRE-FIX USER APPROVAL FAIL:")
  [print(" -",x) for x in e]; raise SystemExit(1)
 print("CB6 PRE-FIX USER APPROVAL PASS: exact change binding and pre-implementation approval verified")
