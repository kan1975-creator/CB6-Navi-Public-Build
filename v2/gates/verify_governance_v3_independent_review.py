#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
old=json.loads((R/"v2/gates/operational_rule_registry_v2.json").read_text())
new=json.loads((R/"v2/gates/operational_rule_registry_v3.json").read_text())
cr=json.loads((R/"v2/gates/user_approval_rule_change_record.json").read_text())
ae=json.loads((R/"v2/gates/user_approval_rule_adoption_evidence.json").read_text())
if old.get("version")!=2 or old.get("status")!="ACTIVE": e.append("prechange registry authority not active v2")
if new.get("version")!=3 or new.get("status")!="ACTIVE": e.append("adopted registry identity invalid")
if new.get("supersedes")!="v2/gates/operational_rule_registry_v2.json": e.append("v3 lineage missing")
if not new.get("change_reason") or not cr.get("reason"): e.append("change reason missing")
rules={x.get("id"):x for x in new.get("rules",[])}
r=rules.get("OPS-USER-APPROVAL-BEFORE-FIX-001",{})
if r.get("status")!="ACTIVE": e.append("approval rule adopted state invalid")
if r.get("contract")!="v2/gates/user_approval_before_fix_contract.json": e.append("approval contract binding missing")
v=set(r.get("verification",[]))
if {"v2/gates/verify_user_approval_before_fix.py","v2/tests/test_user_approval_before_fix_fail_closed.py"}-v: e.append("approval verification binding missing")
p=r.get("proposal",{})
if not all(p.get(k) is True for k in ("approval_reuse_for_different_change_forbidden","post_hoc_approval_forbidden","missing_approval_forbidden","fail_closed")): e.append("approval fail-closed protections weakened")
if new.get("adoption_lifecycle",{}).get("direct_transition_to_active_forbidden") is not True: e.append("direct ACTIVE protection missing")
if ae.get("rule_id")!="OPS-USER-APPROVAL-BEFORE-FIX-001" or ae.get("evidence",{}).get("independent_review",{}).get("conclusion")!="success": e.append("adoption evidence invalid")
if cr.get("active_authority")!="v2/gates/operational_rule_registry_v2.json" or cr.get("candidate")!="v2/gates/operational_rule_registry_v3.json": e.append("change record lineage invalid")
if e:
 print("CB6 GOVERNANCE V3 INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 GOVERNANCE V3 INDEPENDENT REVIEW PASS: prechange=v2; adopted=v3 ACTIVE; approval_rule=ACTIVE; adoption_evidence=verified; lineage=verified; fail_closed=verified")
