#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"v2/monitoring/monitoring_policy.json"; L=ROOT/"v2/monitoring/cycles.jsonl"
def fail(msgs):
 print("CB6 MONITORING POLICY FAIL:")
 for m in msgs: print(" -",m)
 raise SystemExit(1)
p=json.loads(P.read_text(encoding="utf-8"))
errs=[]
if p.get("schema")!=1 or p.get("status")!="ACTIVE": errs.append("active policy invalid")
if p.get("method_version")!=json.loads((ROOT/"v2/gates/development_method_contract.json").read_text()).get("method_version"): errs.append("policy method_version mismatch")
allowed=set(p.get("permitted_no_commit_reasons",[]))
if allowed!={"ACTIONS_WAIT","DEVICE_EVIDENCE_WAIT","SPEC_DECISION_WAIT","PERMISSION_WAIT"}: errs.append("permitted exception set drifted")
rows=[]
for n,line in enumerate(L.read_text(encoding="utf-8").splitlines(),1):
 if not line.strip(): continue
 try: r=json.loads(line)
 except Exception as e: errs.append(f"cycle line {n} invalid JSON: {e}"); continue
 rows.append(r)
 required={"cycle_id","policy_version","started_at","outcome","commit_sha","exception_reason","evidence"}
 if set(r)!=required: errs.append(f"cycle {n} fields invalid"); continue
 if r["policy_version"]!=p["version"]: errs.append(f"cycle {r['cycle_id']} stale policy_version")
 if r["outcome"]=="COMMIT":
  if not re.fullmatch(r"[0-9a-f]{40}",r["commit_sha"] or ""): errs.append(f"cycle {r['cycle_id']} COMMIT lacks 40-hex sha")
  if r["exception_reason"] is not None: errs.append(f"cycle {r['cycle_id']} COMMIT also claims exception")
  if not r["evidence"]: errs.append(f"cycle {r['cycle_id']} COMMIT lacks evidence")
 elif r["outcome"]=="EXTERNAL_WAIT":
  if r["commit_sha"] is not None: errs.append(f"cycle {r['cycle_id']} wait unexpectedly has commit")
  if r["exception_reason"] not in allowed: errs.append(f"cycle {r['cycle_id']} invalid exception {r['exception_reason']!r}")
  if not r["evidence"]: errs.append(f"cycle {r['cycle_id']} exception lacks evidence")
 else: errs.append(f"cycle {r.get('cycle_id')} invalid outcome {r.get('outcome')!r}")
if errs: fail(errs)
print(f"CB6 MONITORING POLICY PASS: policy=v{p['version']}; cycles={len(rows)}; unaccounted=0")
