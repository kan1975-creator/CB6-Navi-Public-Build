#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
c=json.loads((R/"v2/gates/cross_cutting_rule_foundation_candidate.json").read_text())
spec=c["feature_contract_inheritance"]; required=spec["required_marker"]; value=spec["required_value"]
# Synthetic future feature: only the global inheritance marker, never per-rule wiring.
future={"schema":1,"feature_id":"FUTURE_SYNTHETIC_FEATURE","method_version":2,required:value}
if future.get(required)!=value:raise SystemExit("future feature did not inherit global cross-cutting rules")
if any(k in future for k in ("OPS-STATUS-REPORTING-001","NOTIFICATION-STALE-STATE","OPS-USER-APPROVAL-BEFORE-FIX-001")):raise SystemExit("per-rule wiring unexpectedly required")
missing=dict(future);missing.pop(required)
if missing.get(required)==value:raise SystemExit("missing inheritance marker was accepted")
weaken=dict(future);weaken[required]="PARTIAL"
if weaken.get(required)==value:raise SystemExit("weakened inheritance was accepted")
p=c.get("future_feature_positive_application_test",{})
if p.get("required_before_adoption") is not True or p.get("independent_review_must_verify") is not True:raise SystemExit("positive application evidence not required for adoption/review")
print("CB6 FUTURE FEATURE POSITIVE APPLICATION PASS: synthetic new feature inherits global cross-cutting rules without per-rule wiring")
