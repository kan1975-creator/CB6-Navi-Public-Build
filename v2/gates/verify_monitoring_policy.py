#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(msgs):
 print("CB6 MONITORING POLICY FAIL:")
 for m in msgs: print(" -",m)
 raise SystemExit(1)
p=json.loads((ROOT/"v2/gates/monitoring/policy_v1.json").read_text())
if p.get("status")!="ACTIVE" or p.get("version")!=1: fail(["active policy identity invalid"])
mv=json.loads((ROOT/"v2/gates/development_method_contract.json").read_text()).get("method_version")
if p.get("method_version")!=mv: fail([f"policy method_version={p.get('method_version')!r}, required={mv}"])
allowed=set(p.get("allowed_exceptions",[])); expected={"ACTIONS_WAIT","DEVICE_EVIDENCE_WAIT","SPEC_DECISION_WAIT","PERMISSION_WAIT"}
if allowed!=expected: fail(["allowed exception set drifted"])
errors=[]; records=sorted((ROOT/"v2/gates/monitoring/cycles").glob("*.json"))
for f in records:
 d=json.loads(f.read_text())
 outcome=d.get("outcome")
 if d.get("method_version")!=mv: errors.append(f"{f.name}: stale/missing method_version")
 if outcome=="COMMIT":
  if not re.fullmatch(r"[0-9a-f]{40}",str(d.get("commit_sha",""))): errors.append(f"{f.name}: COMMIT lacks valid commit_sha")
  if d.get("exception") not in (None,""): errors.append(f"{f.name}: COMMIT must not claim exception")
 elif outcome=="EXCEPTION":
  if d.get("exception") not in allowed: errors.append(f"{f.name}: invalid/missing exception")
  if not str(d.get("evidence","")).strip(): errors.append(f"{f.name}: exception lacks objective evidence")
  if d.get("commit_sha") not in (None,""): errors.append(f"{f.name}: EXCEPTION must not claim commit")
 else: errors.append(f"{f.name}: missing/invalid outcome")
 for k in ("cycle_id","started_at","basis_head"):
  if not d.get(k): errors.append(f"{f.name}: missing {k}")
if errors: fail(errors)
print(f"CB6 MONITORING POLICY PASS: policy=v{p['version']}; cycles={len(records)}; violations=0")
