#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; d=json.loads((R/"v2/gates/operational_rule_registry_v2.json").read_text()); e=[]
if d.get("version")!=2 or d.get("status")!="CANDIDATE": e.append("registry v2 must remain CANDIDATE before adoption")
if d.get("supersedes")!="v2/gates/operational_rule_registry.json": e.append("v2 supersedes path missing")
if not d.get("change_reason"): e.append("change reason missing")
a=d.get("adoption_lifecycle",{})
if a.get("states")!=["PROPOSED","IMPLEMENTED_UNVERIFIED","MACHINE_VERIFIED","ACTIVE"]: e.append("adoption states mismatch")
if a.get("direct_transition_to_active_forbidden") is not True: e.append("direct ACTIVE transition not forbidden")
if a.get("chat_declaration_is_not_transition_evidence") is not True: e.append("chat declaration accepted as transition evidence")
sp=a.get("authority_split",{})
if sp.get("rule_content_authority")!="explicit_user_decision" or sp.get("mechanism_acceptance_evidence")!="github_gate_evidence": e.append("authority split mismatch")
expected={"PROPOSED":("IMPLEMENTED_UNVERIFIED",{"contract_path","verification_paths"}),"IMPLEMENTED_UNVERIFIED":("MACHINE_VERIFIED",{"destructive_test_path","successful_gate_run_evidence"}),"MACHINE_VERIFIED":("ACTIVE",{"explicit_user_adoption_record","coverage_status_MACHINE_ENFORCED"})}
for src,(dst,req) in expected.items():
 x=a.get("transitions",{}).get(src,{})
 if x.get("to")!=dst or set(x.get("requires",[]))!=req: e.append("invalid transition contract: "+src)
if e:
 print("CB6 RULE ADOPTION LIFECYCLE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 RULE ADOPTION LIFECYCLE PASS: candidate=v2; states=4; direct_active=forbidden; authority_split=verified")
