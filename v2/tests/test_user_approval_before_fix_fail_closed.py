#!/usr/bin/env python3
import importlib.util, pathlib
P=pathlib.Path(__file__).resolve().parents[1]/"gates"/"verify_user_approval_before_fix.py"
s=importlib.util.spec_from_file_location("v",P);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
base={"proposed_change_id":"change-A","implementation_started_at":"2026-09-30T06:00:00Z","approval":{"approval_id":"A-1","approved_at":"2026-09-30T05:59:00Z","proposed_change_id":"change-A","approved_change_summary":"exact change A","github_reference":"commit-message: Approval-Ref=A-1"}}
assert not v.check(base)
cases=[]
x={**base};x["approval"]=None;cases.append(("missing",x,"missing approval"))
x={**base,"approval":dict(base["approval"])};x["approval"]["approved_at"]="2026-09-30T06:01:00Z";cases.append(("post-hoc",x,"approval is not pre-implementation"))
x={**base,"proposed_change_id":"change-B","approval":dict(base["approval"])};cases.append(("reuse",x,"approval binding mismatch"))
for n,d,needle in cases:
 e=v.check(d)
 if needle not in e: raise SystemExit(n+" not rejected: "+repr(e))
 print("PASS expected approval rejection:",n)
print("PASS pre-fix approval destructive cases rejected")
