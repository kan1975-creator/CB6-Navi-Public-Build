#!/usr/bin/env python3
import json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=ROOT/"v2/gates/apk_build_preflight_candidate.json"
d=json.loads(p.read_text())
req=d.get("requirements",{})
required=["latest_authority_checked","pinned_upstream_revalidated","feature_gate_passed","impact_and_research_records_present","generated_source_integration_checked","change_allowlist_checked","frozen_assets_checked","cross_feature_integration_checked","routing_search_favorites_offline_non_regression_checked","diagnostic_path_checked_when_present","audits_and_destructive_tests_passed","diff_check_passed","method_registry_coverage_checked","temporary_diagnostic_separated_from_production"]
errors=[]
if d.get("status")!="PROPOSED": errors.append("candidate must remain PROPOSED")
if d.get("fail_closed") is not True: errors.append("fail_closed must be true")
if d.get("placement")!="immediately_before_gradle_apk_build": errors.append("placement invalid")
for k in required:
    if req.get(k) is not True: errors.append("missing/false requirement: "+k)
for x in ["Method Freeze","Development Gate","Feature Gate","APK Evidence","Device Evidence","OPS-USER-APPROVAL-BEFORE-FIX-001","OPS-DEVELOPMENT-EFFICIENCY-001"]:
    if x not in d.get("non_weakening",[]): errors.append("non-weakening missing: "+x)
if errors:
    print("\n".join(errors)); sys.exit(1)
print("APK Build Preflight candidate contract: PASS")
