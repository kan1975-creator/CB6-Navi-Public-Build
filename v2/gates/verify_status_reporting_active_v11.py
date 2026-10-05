#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v11.json").read_text(encoding="utf-8")); a=json.loads((R/"v2/gates/status_reporting_contract_v10.json").read_text(encoding="utf-8"))
if d.get("schema")!=11 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="ACTIVE": e.append("active v11 identity/status invalid")
for k in a:
 if k not in ("schema","status","source","freshness_rule","activation","revision","adoption") and d.get(k)!=a.get(k): e.append("existing ACTIVE v10 contract changed: "+k)
x=d.get("freshness_rule",{}).get("unknown_run_id_discovery",{})
for k in ("required_when_current_head_known_and_run_id_unknown","discovery_must_include_push_triggered_runs","discovered_run_must_match_current_head_sha","pull_request_only_run_lookup_is_insufficient_for_push_discovery","unsupported_discovery_result_must_not_be_treated_as_run_absence","zero_results_from_incomplete_discovery_is_not_run_nonexistence_evidence"):
 if x.get(k) is not True: e.append("unknown-run discovery guard invalid: "+k)
if x.get("after_run_id_discovery")!="DELEGATE_TO_KNOWN_RUN_ID_DIRECT_REFRESH": e.append("known-run handoff invalid")
if d.get("activation",{}).get("candidate_validation_run_id")!=37383341351 or d.get("activation",{}).get("independent_review_run_id")!=37384389316: e.append("v11 activation evidence invalid")
if d.get("adoption",{}).get("status")!="ADOPTED": e.append("v11 lifecycle not finalized")
ev=json.loads((R/"v2/gates/status_reporting_adoption_evidence_v11.json").read_text(encoding="utf-8"))
if ev.get("status")!="ACTIVE" or ev.get("next_required")!=[]: e.append("v11 adoption evidence still pending")
if e:
 print("CB6 STATUS REPORTING V11 ACTIVE FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 STATUS REPORTING V11 ACTIVE PASS: ACTIVE v10 preserved; unknown Run discovery is push-capable, HEAD-bound and fail-closed")
