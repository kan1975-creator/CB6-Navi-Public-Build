#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
C=ROOT/"v2/gates/future_rule_intake_precheck_candidate.json"
A=ROOT/"v2/gates/operational_rule_registry_v3.json"
d=json.loads(C.read_text()); a=json.loads(A.read_text()); errs=[]
if d.get("status")!="PROPOSED": errs.append("candidate must remain PROPOSED before adoption")
if d.get("target_rule")!="OPS-FUTURE-RULE-INTAKE-001": errs.append("wrong target rule")
rules={r.get("id"):r for r in a.get("rules",[])}
if rules.get("OPS-FUTURE-RULE-INTAKE-001",{}).get("status")!="ACTIVE": errs.append("active intake authority missing")
p=d.get("pre_registration_check",{})
if p.get("required") is not True: errs.append("pre-registration check not mandatory")
required_scopes={"ACTIVE operational rules","CANDIDATE/PROPOSED operational rules","development method authority","governance and cross-cutting rules"}
if not required_scopes.issubset(set(p.get("search_scope",[]))): errs.append("pre-registration search scope incomplete")
o=p.get("outcomes",{})
if o.get("exact_duplicate")!="DO_NOT_CREATE_NEW_RULE; apply existing authority": errs.append("exact duplicate does not block new rule")
if o.get("partial_overlap")!="ADD_ONLY_MISSING_SEMANTICS; preserve existing authority": errs.append("partial overlap may duplicate existing authority")
if o.get("no_overlap")!="NEW_RULE_CANDIDATE_MAY_BE_CREATED": errs.append("no-overlap outcome invalid")
for e in ("current GitHub HEAD","paths/IDs checked","overlap classification"):
 if e not in p.get("evidence_required",[]): errs.append("missing evidence requirement: "+e)
if p.get("chat_memory_only_forbidden") is not True: errs.append("chat-memory-only precheck allowed")
if d.get("direct_active_forbidden") is not True: errs.append("direct ACTIVE transition not blocked")
if errs:
 print("CB6 FUTURE RULE INTAKE PRECHECK CANDIDATE FAIL:")
 for e in errs: print(" -",e)
 raise SystemExit(1)
print("CB6 FUTURE RULE INTAKE PRECHECK CANDIDATE PASS")
