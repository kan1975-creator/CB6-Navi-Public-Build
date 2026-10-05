#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; e=[]
n=json.loads((R/"v2/gates/status_reporting_contract_v11_candidate.json").read_text(encoding="utf-8"))
o=json.loads((R/"v2/gates/status_reporting_contract_v10.json").read_text(encoding="utf-8"))
if n.get("schema")!=11 or n.get("status")!="CANDIDATE" or n.get("rule_id")!="OPS-STATUS-REPORTING-001": e.append("v11 candidate identity/status invalid")
for k in o:
 if k not in ("schema","status","source","freshness_rule","activation","revision","adoption") and n.get(k)!=o.get(k): e.append("ACTIVE v10 non-freshness behavior changed: "+k)
for k,v in o.get("freshness_rule",{}).items():
 if n.get("freshness_rule",{}).get(k)!=v: e.append("existing v10 freshness rule changed: "+k)
x=n.get("freshness_rule",{}).get("unknown_run_id_discovery",{})
for k in ("required_when_current_head_known_and_run_id_unknown","discovery_must_include_push_triggered_runs","discovered_run_must_match_current_head_sha","pull_request_only_run_lookup_is_insufficient_for_push_discovery","unsupported_discovery_result_must_not_be_treated_as_run_absence","zero_results_from_incomplete_discovery_is_not_run_nonexistence_evidence"):
 if x.get(k) is not True: e.append("unknown-run discovery guard invalid: "+k)
if x.get("after_run_id_discovery")!="DELEGATE_TO_KNOWN_RUN_ID_DIRECT_REFRESH": e.append("v10 direct-refresh handoff missing")
if n.get("activation",{}).get("status")!="CANDIDATE" or n.get("adoption",{}).get("status")!="NOT_ADOPTED": e.append("candidate self-activation detected")
for q in ("successful_candidate_gate","independent_review","explicit_user_adoption","registry_and_coverage_machine_enforcement"):
 if q not in n.get("adoption",{}).get("required_before_active",[]): e.append("activation prerequisite missing: "+q)
if e:
 print("CB6 STATUS REPORTING V11 CANDIDATE FAIL:"); [print(" -",x) for x in e]; raise SystemExit(1)
print("CB6 STATUS REPORTING V11 CANDIDATE PASS: ACTIVE v10 preserved; unknown current-HEAD Run discovery includes push and fails closed on incomplete discovery")
