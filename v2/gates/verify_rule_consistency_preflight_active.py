#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/rule_consistency_preflight_active.json").read_text(encoding="utf-8"))
if d.get("rule_id")!="OPS-RULE-CONSISTENCY-PREFLIGHT-001" or d.get("status")!="ACTIVE": e.append("active identity/status invalid")
r=d.get("requirements",{})
for k in ("github_current_authority_must_be_checked","existing_rule_reuse_or_extension_preferred_when_sufficient","unresolved_conflict_blocks_rule_progression","chat_memory_alone_forbidden"):
 if r.get(k) is not True: e.append("preflight guard invalid: "+k)
for x in ("current ACTIVE operational rule registry","applicable prior rule versions","related contracts","related verifier and destructive tests","rule coverage","method freeze when relevant"):
 if x not in r.get("required_preflight_sources",[]): e.append("preflight source missing: "+x)
for x in ("already_governed","duplicate","conflict","extension_needed","new_rule_needed"):
 if x not in r.get("required_decisions",[]): e.append("preflight decision missing: "+x)
reg=json.loads((R/"v2/gates/operational_rule_registry_v11.json").read_text(encoding="utf-8"))
if reg.get("status")!="ACTIVE" or reg.get("revision_policy",{}).get("in_place_change_forbidden") is not True: e.append("existing registry revision authority not preserved")
rr=json.loads((R/"v2/gates/operational_rule_registry_v12.json").read_text()); row={x.get("id"):x for x in rr["rules"]}.get("OPS-RULE-CONSISTENCY-PREFLIGHT-001",{})
if rr.get("version")!=12 or row.get("contract")!="v2/gates/rule_consistency_preflight_active.json": e.append("registry v12 rule-consistency binding invalid")
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text()); ce={x.get("rule_id"):x for x in cov["entries"]}
if cov.get("registry")!="v2/gates/operational_rule_registry_v12.json" or ce.get("OPS-RULE-CONSISTENCY-PREFLIGHT-001",{}).get("coverage_status")!="MACHINE_ENFORCED": e.append("rule-consistency machine coverage missing")
if e:
 print("CB6 RULE CONSISTENCY PREFLIGHT ACTIVE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 RULE CONSISTENCY PREFLIGHT ACTIVE PASS: prior/current GitHub rules must be checked for governed/duplicate/conflict/extension/new before rule progression")
