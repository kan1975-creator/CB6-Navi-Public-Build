#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v10.json").read_text(encoding="utf-8")); a=json.loads((R/"v2/gates/status_reporting_contract_v9.json").read_text(encoding="utf-8"))
if d.get("schema")!=10 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v10 identity/status invalid")
for k in a:
 if k not in ("schema","status","source","freshness_rule","activation","revision","adoption") and d.get(k)!=a.get(k): e.append("existing ACTIVE v9 contract changed: "+k)
x=d.get("freshness_rule",{}).get("known_run_id_direct_refresh",{})
for k in ("required_when_tracking_run_id_known","direct_run_refresh_has_priority","run_list_is_supplementary","absence_from_run_list_is_not_state_change_evidence"):
 if x.get(k) is not True: e.append("known-run direct-refresh guard invalid: "+k)
for k in ("run_deleted","run_completed","run_failed","run_state_changed"):
 if k not in x.get("forbidden_inferences_from_list_absence",[]): e.append("forbidden list-absence inference missing: "+k)
if d.get("adoption",{}).get("candidate_validation_run_id")!=37340389327 or d.get("adoption",{}).get("independent_review_run_id")!=37340923837: e.append("v10 adoption evidence invalid")
if d.get("activation",{}).get("status")!="ACTIVE" or d.get("adoption",{}).get("status")!="ADOPTED": e.append("v10 lifecycle not finalized")
ev=json.loads((R/"v2/gates/status_reporting_adoption_evidence_v10.json").read_text(encoding="utf-8"))
if ev.get("status")!="ACTIVE" or ev.get("next_required")!=[]: e.append("v10 adoption evidence still pending")
if e:
 print("CB6 STATUS REPORTING V10 ACTIVE FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 STATUS REPORTING V10 ACTIVE PASS: ACTIVE v9 preserved; known tracked Run IDs require direct refresh; list absence alone cannot change state")
