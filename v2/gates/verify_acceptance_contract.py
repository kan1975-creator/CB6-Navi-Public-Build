#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(m): print("CB6 ACCEPTANCE CONTRACT FAIL:",m); raise SystemExit(1)
if len(sys.argv)!=2: fail("usage: verify_acceptance_contract.py <feature_id>")
fid=sys.argv[1]
reg=json.loads((ROOT/"v2/gates/acceptance_seals.json").read_text())
rows=[x for x in reg.get("seals",[]) if x.get("feature_id")==fid and x.get("status")=="ACTIVE"]
if len(rows)!=1: fail("exactly one active acceptance seal required")
r=rows[0]; p=ROOT/r["path"]
if not p.is_file(): fail("sealed acceptance contract missing")
cp=subprocess.run(["git","hash-object",str(p.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
if cp.returncode or cp.stdout.strip()!=r.get("blob_sha"): fail("sealed acceptance contract changed in place")
d=json.loads(p.read_text())
if d.get("schema")!=1 or d.get("feature_id")!=fid or d.get("version")!=r.get("version") or d.get("status")!="SEALED": fail("contract identity/version invalid")
criteria=d.get("criteria",[])
if not criteria or any(set(x)!={"id","observable"} or not x["id"] or not x["observable"] for x in criteria): fail("observable criteria invalid")
if len({x["id"] for x in criteria})!=len(criteria): fail("duplicate criteria")
raw=d.get("raw_evidence_policy",{})
if raw.get("prose_only_forbidden") is not True or not raw.get("allowed"): fail("raw evidence policy is not fail-closed")
ind=d.get("independent_review_policy",{})
if ind!={"separate_session_required":True,"implementation_intent_withheld":True,"criteria_and_raw_evidence_only":True}: fail("independent review policy weakened")
rev=d.get("revision_policy",{})
if rev!={"in_place_change_forbidden":True,"new_version_required":True,"reason_required":True,"independent_reapproval_required":True}: fail("revision policy weakened")
print("CB6 ACCEPTANCE CONTRACT PASS:",fid,"v"+str(d["version"]),r["blob_sha"])
