#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
old=json.loads((R/"v2/gates/operational_rule_registry.json").read_text())
new=json.loads((R/"v2/gates/operational_rule_registry_v2.json").read_text())
mr=json.loads((R/"v2/gates/method_revision_procedure_v1.json").read_text())
ra=json.loads((R/"v2/gates/rule_adoption_change_record.json").read_text())
mc=json.loads((R/"v2/gates/method_revision_change_record.json").read_text())
if old.get("version")!=1: e.append("prechange registry authority not v1")
if new.get("version")!=2 or new.get("status") not in ("CANDIDATE","ACTIVE"): e.append("registry candidate/adopted identity invalid")
if new.get("supersedes")!="v2/gates/operational_rule_registry.json": e.append("registry lineage missing")
if not new.get("change_reason") or not ra.get("reason"): e.append("registry change reason missing")
if mr.get("status") not in ("CANDIDATE","INDEPENDENTLY_REVIEWED","ACTIVE_REFROZEN") or not mc.get("reason"): e.append("method revision candidate/adopted reason missing")
if ra.get("active_registry_unchanged") is not True or mc.get("active_method_unchanged") is not True or mc.get("freeze_lock_unchanged") is not True: e.append("pre-adoption authority was modified")
if new.get("adoption_lifecycle",{}).get("authority_split",{}).get("rule_content_authority")!="explicit_user_decision": e.append("user authority lost")
if mr.get("invariants",{}).get("candidate_cannot_verify_its_own_adoption") is not True: e.append("self-adoption protection missing")
if e:
 print("CB6 GOVERNANCE INDEPENDENT REVIEW FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print("CB6 GOVERNANCE INDEPENDENT REVIEW PASS: old_registry=v1; candidate_registry=v2; reasons=present; active_authority=unchanged; self_adoption=blocked")
