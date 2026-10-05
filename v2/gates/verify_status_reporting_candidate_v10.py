#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_candidate_v10.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v9.json").read_text(encoding="utf-8"))
if d.get("schema")!=10 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v10 identity/status invalid")
for k in a:
 if k not in ("schema","status","source","freshness_rule","activation","revision","adoption") and d.get(k)!=a.get(k): e.append("existing ACTIVE v9 contract changed: "+k)
f=d.get("freshness_rule",{})
for k in ("progress_query_requires_current_head","progress_query_requires_relevant_run","material_log_evidence_requires_fresh_raw_log"):
 if f.get(k) is not True: e.append("existing freshness guard changed: "+k)
x=f.get("known_run_id_direct_refresh",{})
for k in ("required_when_tracking_run_id_known","direct_run_refresh_has_priority","run_list_is_supplementary","absence_from_run_list_is_not_state_change_evidence"):
 if x.get(k) is not True: e.append("known-run direct-refresh guard invalid: "+k)
for k in ("run_deleted","run_completed","run_failed","run_state_changed"):
 if k not in x.get("forbidden_inferences_from_list_absence",[]): e.append("forbidden list-absence inference missing: "+k)
if d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V10 CANDIDATE FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 STATUS REPORTING V10 CANDIDATE PASS: ACTIVE v9 preserved; known tracked Run IDs require direct refresh and list absence alone cannot change state")
