#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(m): raise SystemExit("CB6 INDEPENDENT REVIEW FAIL: "+m)
if len(sys.argv)!=2: fail("usage: verify_independent_review.py <feature_id>")
fid=sys.argv[1]
p=ROOT/f"v2/gates/independent_review/{fid}.json"
if not p.is_file(): fail("independent review evidence missing")
d=json.loads(p.read_text())
required={"schema","feature_id","target_commit","checklist","review_context","implementation_context_shared","result","evidence"}
missing=sorted(required-set(d))
if missing: fail("fields missing: "+",".join(missing))
if d.get("schema")!=1 or d.get("feature_id")!=fid: fail("identity invalid")
sha=d.get("target_commit","")
if not isinstance(sha,str) or len(sha)!=40 or any(c not in "0123456789abcdef" for c in sha): fail("target_commit invalid")
if d.get("checklist")!="v2/governance/audit_checklist_v1.md": fail("wrong checklist")
if not d.get("review_context"): fail("review_context missing")
if d.get("implementation_context_shared") is not False: fail("review was not independent")
if d.get("result")!="ACCEPTED": fail("review not accepted")
ev=d.get("evidence")
if not isinstance(ev,list) or not ev or any(not isinstance(x,str) or not x.strip() for x in ev): fail("traceable evidence missing")
print("CB6 INDEPENDENT REVIEW PASS:",fid,sha)
