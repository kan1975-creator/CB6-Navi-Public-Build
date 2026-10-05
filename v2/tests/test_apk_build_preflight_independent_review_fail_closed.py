#!/usr/bin/env python3
import copy,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2]
d=json.loads((R/"v2/gates/apk_build_preflight_independent_review.json").read_text())
keys=["existing_active_authority_unchanged","no_apk_workflow_connection","no_method_weakening","no_feature_gate_weakening","no_apk_or_device_evidence_weakening","explicit_user_adoption_still_required"]
def ok(x): return x.get("status")=="INDEPENDENT_REVIEW_CANDIDATE" and all(x["checks"].get(k) is True for k in keys) and x["checks"].get("candidate_gate_result")=="SUCCESS" and x["checks"].get("development_gate_result")=="SUCCESS"
assert ok(d)
for k in keys:
 x=copy.deepcopy(d);x["checks"][k]=False;assert not ok(x),k
x=copy.deepcopy(d);x["checks"]["candidate_gate_result"]="FAILURE";assert not ok(x)
print("APK Build Preflight independent review destructive tests: PASS")
