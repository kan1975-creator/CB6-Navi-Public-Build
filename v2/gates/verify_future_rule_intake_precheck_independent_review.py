#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/future_rule_intake_precheck_candidate.json").read_text(encoding="utf-8"))
if d.get("candidate_id")!="OPS-FUTURE-RULE-INTAKE-PRECHECK-001" or d.get("status")!="PROPOSED": e.append("candidate identity/status invalid")
p=d.get("pre_registration_check",{})
expected=["already_governed","duplicate","conflict","extension_needed","new_rule_needed"]
if p.get("required_classification")!=expected: e.append("five-way classification invalid")
for x in ("current GitHub HEAD","paths/IDs checked","five-way classification"):
 if x not in p.get("evidence_required",[]): e.append("evidence requirement missing: "+x)
if p.get("chat_memory_only_forbidden") is not True or p.get("chat_only_completion_forbidden") is not True: e.append("chat-only authority allowed")
o=p.get("outcomes",{})
if set(o)!=set(expected) or not str(o.get("conflict","")).startswith("FAIL_CLOSED"): e.append("five-way outcomes invalid")
h=d.get("auditor_handoff",{})
if h.get("required_for")!=["extension_needed","new_rule_needed"] or h.get("target")!="CB6-DEVELOPMENT-AUDITOR-V2 change-bound Work Unit": e.append("Auditor V2 handoff invalid")
if h.get("work_unit_identity_required") is not True or h.get("approval_boundary_must_be_preserved") is not True or h.get("auditor_v2_logic_change_forbidden") is not True: e.append("Auditor V2 handoff guards weakened")
if d.get("direct_active_forbidden") is not True: e.append("direct ACTIVE allowed")
if e:
 print("CB6 FUTURE RULE INTAKE PRECHECK INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 FUTURE RULE INTAKE PRECHECK INDEPENDENT REVIEW PASS")
