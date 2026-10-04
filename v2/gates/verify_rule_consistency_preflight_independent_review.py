#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/rule_consistency_preflight_candidate.json").read_text(encoding="utf-8"))
if d.get("rule_id")!="OPS-RULE-CONSISTENCY-PREFLIGHT-001" or d.get("status")!="CANDIDATE": e.append("candidate identity/status invalid")
r=d.get("requirements",{})
for k in ("github_current_authority_must_be_checked","existing_rule_reuse_or_extension_preferred_when_sufficient","unresolved_conflict_blocks_rule_progression","chat_memory_alone_forbidden"):
 if r.get(k) is not True: e.append("preflight guard invalid: "+k)
for x in ("current ACTIVE operational rule registry","applicable prior rule versions","related contracts","related verifier and destructive tests","rule coverage","method freeze when relevant"):
 if x not in r.get("required_preflight_sources",[]): e.append("preflight source missing: "+x)
for x in ("already_governed","duplicate","conflict","extension_needed","new_rule_needed"):
 if x not in r.get("required_decisions",[]): e.append("preflight decision missing: "+x)
reg=json.loads((R/"v2/gates/operational_rule_registry_v11.json").read_text(encoding="utf-8"))
if reg.get("status")!="ACTIVE" or reg.get("revision_policy",{}).get("in_place_change_forbidden") is not True: e.append("existing registry revision authority not preserved")
if d.get("activation",{}).get("direct_active_forbidden") is not True or d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 RULE CONSISTENCY PREFLIGHT INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 RULE CONSISTENCY PREFLIGHT INDEPENDENT REVIEW PASS: prior/current GitHub rules must be checked for governed/duplicate/conflict/extension/new before rule progression")
