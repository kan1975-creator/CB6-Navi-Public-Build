#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
d=json.loads((R/"v2/gates/status_reporting_contract_v11_candidate.json").read_text(encoding="utf-8"))
a=json.loads((R/"v2/gates/status_reporting_contract_v10.json").read_text(encoding="utf-8"))
if d.get("schema")!=11 or d.get("rule_id")!="OPS-STATUS-REPORTING-001" or d.get("status")!="CANDIDATE": e.append("candidate v11 identity/status invalid")
for k in a:
 if k not in ("schema","status","source","freshness_rule","activation","revision","adoption") and d.get(k)!=a.get(k): e.append("ACTIVE v10 behavior changed: "+k)
for k,v in a.get("freshness_rule",{}).items():
 if d.get("freshness_rule",{}).get(k)!=v: e.append("ACTIVE v10 freshness changed: "+k)
x=d.get("freshness_rule",{}).get("unknown_run_id_discovery",{})
for k in ("required_when_current_head_known_and_run_id_unknown","discovery_must_include_push_triggered_runs","discovered_run_must_match_current_head_sha","pull_request_only_run_lookup_is_insufficient_for_push_discovery","unsupported_discovery_result_must_not_be_treated_as_run_absence","zero_results_from_incomplete_discovery_is_not_run_nonexistence_evidence"):
 if x.get(k) is not True: e.append("unknown-run independent guard invalid: "+k)
if x.get("after_run_id_discovery")!="DELEGATE_TO_KNOWN_RUN_ID_DIRECT_REFRESH": e.append("direct-refresh handoff missing")
if d.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation allowed")
if e:
 print("CB6 STATUS REPORTING V11 INDEPENDENT REVIEW FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 STATUS REPORTING V11 INDEPENDENT REVIEW PASS: ACTIVE v10 preserved; unknown Run discovery is push-capable, HEAD-bound and fail-closed")
