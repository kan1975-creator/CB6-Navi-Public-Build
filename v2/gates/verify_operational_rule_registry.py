#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; P=ROOT/"v2/gates/operational_rule_registry_v12.json"
d=json.loads(P.read_text()); errs=[]
mv=json.loads((ROOT/"v2/gates/development_method_contract.json").read_text()).get("method_version")
if d.get("method_version")!=mv: errs.append("registry method_version mismatch")
if d.get("status")!="ACTIVE": errs.append("registry is not ACTIVE")
if d.get("adoption_evidence")!="v2/gates/user_approval_rule_adoption_evidence.json": errs.append("adoption evidence link missing")
ip=d.get("intake_policy",{})
for k in ("continuing_request_must_be_registered","chat_memory_is_not_authority","active_rule_requires_machine_verification","active_rule_requires_github_verification_source","proposed_rule_must_not_enter_coverage","unverifiable_operational_promise_remains_proposed"):
 if ip.get(k) is not True: errs.append("intake policy weakened: "+k)
seen=set()
for r in d.get("rules",[]):
 rid=r.get("id")
 if not rid or rid in seen: errs.append("missing/duplicate rule id: "+str(rid))
 seen.add(rid)
 status=r.get("status")
 if status=="PROPOSED":
  continue
 if status!="ACTIVE":
  errs.append(f"{rid}: unsupported status: {status}")
  continue
 for k in ("scope","source","contract"):
  if not r.get(k): errs.append(f"{rid}: missing {k}")
 c=ROOT/str(r.get("contract",""))
 if not c.is_file(): errs.append(f"{rid}: contract missing: {r.get('contract')}")
 vv=r.get("verification")
 if not isinstance(vv,list) or not vv: errs.append(f"{rid}: ACTIVE rule lacks machine verification"); continue
 for v in vv:
  if not isinstance(v,str) or not v.startswith("v2/"):
   errs.append(f"{rid}: verification source is not a GitHub repository path: {v}")
  elif not (ROOT/v).is_file(): errs.append(f"{rid}: verifier missing: {v}")
if not d.get("rules"): errs.append("rule registry empty")
if errs:
 print("CB6 OPERATIONAL RULE REGISTRY FAIL:")
 for e in errs: print(" -",e)
 raise SystemExit(1)
print(f"CB6 OPERATIONAL RULE REGISTRY PASS: active_rules={sum(r.get('status')=='ACTIVE' for r in d['rules'])}; proposed_rules={sum(r.get('status')=='PROPOSED' for r in d['rules'])}; uncovered=0")
