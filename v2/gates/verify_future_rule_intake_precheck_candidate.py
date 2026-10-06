#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
C=ROOT/"v2/gates/future_rule_intake_precheck_candidate.json"
A=ROOT/"v2/gates/operational_rule_registry_v3.json"
d=json.loads(C.read_text()); a=json.loads(A.read_text()); errs=[]
if d.get("schema")!=2: errs.append("candidate schema must be 2")
if d.get("status")!="PROPOSED": errs.append("candidate must remain PROPOSED before adoption")
if d.get("target_rule")!="OPS-FUTURE-RULE-INTAKE-001": errs.append("wrong target rule")
rules={r.get("id"):r for r in a.get("rules",[])}
if rules.get("OPS-FUTURE-RULE-INTAKE-001",{}).get("status")!="ACTIVE": errs.append("active intake authority missing")
p=d.get("pre_registration_check",{})
if p.get("required") is not True: errs.append("pre-registration check not mandatory")
required_scopes={"ACTIVE operational rules","CANDIDATE/PROPOSED operational rules","development method authority","governance and cross-cutting rules"}
if not required_scopes.issubset(set(p.get("search_scope",[]))): errs.append("pre-registration search scope incomplete")
o=p.get("outcomes",{})
required_outcomes={
 "already_governed":"APPLY_EXISTING_AUTHORITY; record authority IDs/paths; do not end on chat memory alone",
 "duplicate":"DO_NOT_CREATE_NEW_RULE; apply existing authority; record authority IDs/paths",
 "conflict":"FAIL_CLOSED; do not progress until conflict is resolved",
 "extension_needed":"ADD_ONLY_MISSING_SEMANTICS; create or update a change-bound candidate Work Unit",
 "new_rule_needed":"CREATE_NEW_RULE_CANDIDATE; create a change-bound candidate Work Unit"
}
if o!=required_outcomes: errs.append("five-way intake outcomes incomplete or weakened")
if p.get("required_classification")!=["already_governed","duplicate","conflict","extension_needed","new_rule_needed"]: errs.append("five-way classification not mandatory")
for e in ("current GitHub HEAD","paths/IDs checked","five-way classification"):
 if e not in p.get("evidence_required",[]): errs.append("missing evidence requirement: "+e)
if p.get("chat_only_completion_forbidden") is not True: errs.append("chat-only continuing-rule completion allowed")
h=d.get("auditor_handoff",{})
if h.get("required_for")!=["extension_needed","new_rule_needed"]: errs.append("Auditor handoff outcomes incomplete")
if h.get("target")!="CB6-DEVELOPMENT-AUDITOR-V2 change-bound Work Unit" or h.get("work_unit_identity_required") is not True: errs.append("Auditor V2 Work Unit handoff missing")
if h.get("approval_boundary_must_be_preserved") is not True or h.get("auditor_v2_logic_change_forbidden") is not True: errs.append("Auditor handoff boundary weakened")
if p.get("chat_memory_only_forbidden") is not True: errs.append("chat-memory-only precheck allowed")
if d.get("direct_active_forbidden") is not True: errs.append("direct ACTIVE transition not blocked")
if errs:
 print("CB6 FUTURE RULE INTAKE PRECHECK CANDIDATE FAIL:")
 for e in errs: print(" -",e)
 raise SystemExit(1)
print("CB6 FUTURE RULE INTAKE PRECHECK CANDIDATE PASS")
