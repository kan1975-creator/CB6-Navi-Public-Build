#!/usr/bin/env python3
import json, pathlib, sys
R=pathlib.Path(__file__).resolve().parents[2]
c=json.loads((R/"v2/gates/apk_build_preflight_candidate.json").read_text())
r=json.loads((R/"v2/gates/apk_build_preflight_independent_review.json").read_text())
e=[]
if c.get("status")!="PROPOSED": e.append("candidate not PROPOSED")
if r.get("status")!="INDEPENDENT_REVIEW_CANDIDATE": e.append("review status invalid")
if r.get("candidate")!="v2/gates/apk_build_preflight_candidate.json": e.append("candidate binding invalid")
for k in ["existing_active_authority_unchanged","no_apk_workflow_connection","no_method_weakening","no_feature_gate_weakening","no_apk_or_device_evidence_weakening","explicit_user_adoption_still_required"]:
    if r.get("checks",{}).get(k) is not True: e.append("review invariant failed: "+k)
if r.get("checks",{}).get("candidate_gate_result")!="SUCCESS": e.append("candidate gate evidence missing")
if r.get("checks",{}).get("development_gate_result")!="SUCCESS": e.append("development gate evidence missing")
if e: print("\n".join(e)); sys.exit(1)
print("APK Build Preflight independent review: PASS")
