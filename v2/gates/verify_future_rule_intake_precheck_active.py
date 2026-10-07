#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
d=json.loads((R/"v2/gates/future_rule_intake_precheck_active.json").read_text(encoding="utf-8"))
if d.get("candidate_id")!="OPS-FUTURE-RULE-INTAKE-PRECHECK-001" or d.get("status")!="ACTIVE":e.append("ACTIVE identity/status")
p=d.get("pre_registration_check",{})
if p.get("required_classification")!=["already_governed","duplicate","conflict","extension_needed","new_rule_needed"]:e.append("five-way classification")
for x in ("current GitHub HEAD","paths/IDs checked","five-way classification"):
 if x not in p.get("evidence_required",[]):e.append("evidence:"+x)
if p.get("chat_memory_only_forbidden") is not True or p.get("chat_only_completion_forbidden") is not True:e.append("chat-only guard")
h=d.get("auditor_handoff",{})
if h.get("required_for")!=["extension_needed","new_rule_needed"] or h.get("target")!="CB6-DEVELOPMENT-AUDITOR-V2 change-bound Work Unit":e.append("Auditor V2 handoff")
if h.get("work_unit_identity_required") is not True or h.get("approval_boundary_must_be_preserved") is not True or h.get("auditor_v2_logic_change_forbidden") is not True:e.append("Auditor V2 handoff guards")
if d.get("direct_active_forbidden") is not True:e.append("direct ACTIVE guard")
a=d.get("activation",{})
if a.get("status")!="ACTIVE" or a.get("candidate_gate_run_id")!=37610714841 or a.get("independent_review_run_id")!=37611897404:e.append("activation evidence")
if d.get("adoption",{}).get("status")!="ADOPTED":e.append("adoption")
ev=json.loads((R/"v2/gates/future_rule_intake_precheck_adoption_evidence.json").read_text(encoding="utf-8"))
if ev.get("status")!="ACTIVE":e.append("adoption evidence status")
if e:
 print("CB6 FUTURE RULE INTAKE PRECHECK ACTIVE FAIL:");[print(" -",x) for x in e];raise SystemExit(1)
print("CB6 FUTURE RULE INTAKE PRECHECK ACTIVE PASS")
