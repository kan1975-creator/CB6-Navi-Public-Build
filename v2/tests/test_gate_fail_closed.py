#!/usr/bin/env python3
"""Destructive tests for CB6 gate invariants using isolated repository copies."""
import json, shutil, subprocess, tempfile, os
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]
CASES=[]

def mutate_missing_trace(r):
 p=r/"v2/gates/traceability.json"; d=json.loads(p.read_text()); d["traces"]=[x for x in d["traces"] if x["decision_id"]!="SIG-200M-001"]; p.write_text(json.dumps(d))
CASES.append(("missing-active-decision", mutate_missing_trace, "active decisions absent from traceability"))

def mutate_bypass(r):
 p=r/".github/workflows/test_bypass.yml"; p.write_text("""name: bypass
on:
  push:
    branches: [cb6-v2-clean]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: ./gradlew assemble
""")
CASES.append(("gate-less-workflow", mutate_bypass, "workflow bypasses feature gate"))

def mutate_superseded(r):
 p=r/"v2/gates/traceability.json"; d=json.loads(p.read_text())
 d["traces"].append({"decision_id":"SIG-200M-LEGACY-001","state":"consumed","design_ref":"docs/CB6_DEVELOPMENT_EXECUTION_GATE.md","verification":["destructive fixture"]})
 p.write_text(json.dumps(d))
CASES.append(("superseded-consumed", mutate_superseded, "superseded decision consumed"))

def mutate_bad_spec(r):
 p=r/"v2/gates/current_spec.json"; d=json.loads(p.read_text()); d["signal"]["display"]["zoom_symbols"]["15"]="ghost"; p.write_text(json.dumps(d))
CASES.append(("invalid-current-spec", mutate_bad_spec, "symbol without dimensions"))

def mutate_retired(r):
 p=r/"docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md"; p.write_text(p.read_text().replace("RETIRED AS CANONICAL","CANONICAL AGAIN"))
CASES.append(("retired-design-reactivated", mutate_retired, "retired design lost retirement marker"))

def mutate_fake_implementation_enabled(r):
 p=r/"v2/gates/project_state.json"; d=json.loads(p.read_text())
 d["stage"]="IMPLEMENTATION_ENABLED"; d["feature_builds_allowed"]=True; d["design_verified"]=True
 d["canonical_design"]="docs/CB6_DEVELOPMENT_EXECUTION_GATE.md"; p.write_text(json.dumps(d))
 a=r/"v2/gates/authority_policy.json"; ad=json.loads(a.read_text()); ad["stage"]="IMPLEMENTATION_ENABLED"; a.write_text(json.dumps(ad))
 e=r/"v2/gates/evidence_inventory.json"; ed=json.loads(e.read_text()); ed["stage"]="IMPLEMENTATION_ENABLED"; e.write_text(json.dumps(ed))
 t=r/"v2/gates/traceability.json"; td=json.loads(t.read_text()); td["stage"]="IMPLEMENTATION_ENABLED"; t.write_text(json.dumps(td))
CASES.append(("implementation-with-pending-decisions", mutate_fake_implementation_enabled, "implementation enabled with unconsumed active decisions"))

def mutate_historical_resource_inventory(r):
 p=r/"v2/audits/audit_signals.py"; s=p.read_text()
 s=s.replace("symbols = ['cb6-signal-'+s for s in sorted(set(spec['display']['zoom_symbols'].values()) | set(spec['display']['forward_zoom_symbols'].values()))]", "symbols = ['cb6-signal-'+s for s in spec['display']['symbols']]")
 p.write_text(s)
CASES.append(("historical-resource-inventory", mutate_historical_resource_inventory, "historical resource inventory"))

def mutate_missing_evidence(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 next(x for x in d["decisions"] if x["id"]=="PROC-001")["evidence"]=["docs/DOES_NOT_EXIST.md"]
 p.write_text(json.dumps(d))
CASES.append(("missing-evidence", mutate_missing_evidence, "evidence path missing"))

def mutate_uninventoried_evidence(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 marker=r/"docs/UNINVENTORIED_EVIDENCE_FIXTURE.md"; marker.write_text("destructive fixture only")
 next(x for x in d["decisions"] if x["id"]=="PROC-001")["evidence"]=["docs/UNINVENTORIED_EVIDENCE_FIXTURE.md"]
 p.write_text(json.dumps(d))
CASES.append(("uninventoried-decision-evidence", mutate_uninventoried_evidence, "evidence absent from inventory"))

def mutate_retired_direct_evidence(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 next(x for x in d["decisions"] if x["id"]=="PROC-001")["evidence"]=["docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md"]
 p.write_text(json.dumps(d))
CASES.append(("retired-direct-requirement-evidence", mutate_retired_direct_evidence, "active decision relies directly on retired evidence"))

def mutate_fake_evidence_revalidation(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text())
 x=next(x for x in d["evidence"] if x["status"]=="revalidation-required")
 x["revalidation"]={"state":"validated","record":"","verification":[]}
 p.write_text(json.dumps(d))
CASES.append(("fake-evidence-revalidation", mutate_fake_evidence_revalidation, "validated evidence lacks revalidation record/verification"))

def mutate_invalid_revalidation_state(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text())
 x=next(x for x in d["evidence"] if x["status"]=="revalidation-required")
 x["revalidation"]["state"]="assumed-valid"
 p.write_text(json.dumps(d))
CASES.append(("invalid-evidence-revalidation-state", mutate_invalid_revalidation_state, "invalid evidence revalidation state"))

def mutate_missing_historical_mixed_policy(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text())
 x=next(x for x in d["evidence"] if x["status"]=="historical-mixed")
 x.pop("clause_policy",None)
 p.write_text(json.dumps(d))
CASES.append(("missing-historical-mixed-policy", mutate_missing_historical_mixed_policy, "historical-mixed evidence lacks clause policy"))

def mutate_duplicate_owner(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 x=next(x for x in d["decisions"] if x["id"]=="SIG-COVERAGE-001"); x["spec_key"]="signal.display.200m"
 p.write_text(json.dumps(d))
CASES.append(("duplicate-active-spec-owner", mutate_duplicate_owner, "multiple active owners for spec_key"))

def mutate_broken_supersession(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 next(x for x in d["decisions"] if x["id"]=="SIG-200M-LEGACY-001")["superseded_by"]="SIG-COVERAGE-001"
 p.write_text(json.dumps(d))
CASES.append(("broken-supersession", mutate_broken_supersession, "non-reciprocal supersession"))

def mutate_historical_authority(r):
 p=r/"docs/CB6_V2_MODULE_CONTRACTS.md"; p.write_text(p.read_text()+"\nStatus: CANONICAL IMPLEMENTATION BOUNDARIES\n")
CASES.append(("historical-authority-regained", mutate_historical_authority, "historical document regained authority"))

def mutate_stale_signal_authority(r):
 p=r/"docs/CB6_FROZEN_FEATURES.md"; p.write_text(p.read_text()+"\nThe Run #65 feature above remains the behavioral authority.\n")
CASES.append(("stale-signal-authority-regained", mutate_stale_signal_authority, "historical document regained authority"))

def mutate_evidence_missing_path(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"][0]["path"]="docs/DOES_NOT_EXIST_EVIDENCE.md"; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-missing-path", mutate_evidence_missing_path, "evidence inventory path missing"))

def mutate_evidence_bad_status(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"][0]["status"]="trusted-because-old"; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-bad-status", mutate_evidence_bad_status, "invalid evidence status"))

def mutate_evidence_duplicate_id(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"][1]["id"]=d["evidence"][0]["id"]; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-duplicate-id", mutate_evidence_duplicate_id, "evidence IDs missing/duplicated"))

def mutate_evidence_stage_mismatch(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["stage"]="WRONG_STAGE"; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-stage-mismatch", mutate_evidence_stage_mismatch, "evidence inventory stage/schema mismatch"))

def mutate_evidence_empty(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"]=[]; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-empty", mutate_evidence_empty, "evidence IDs missing/duplicated"))

def mutate_evidence_duplicate_path(r):
 p=r/"v2/gates/evidence_inventory.json"; d=json.loads(p.read_text()); d["evidence"][1]["path"]=d["evidence"][0]["path"]; p.write_text(json.dumps(d))
CASES.append(("evidence-inventory-duplicate-path", mutate_evidence_duplicate_path, "evidence paths missing/duplicated"))

def mutate_active_uses_stale_evidence(r):
 p=r/"v2/gates/active_decisions.json"; d=json.loads(p.read_text())
 next(x for x in d["decisions"] if x["id"]=="PROC-001")["evidence"]=["docs/CB6_V2_CROSS_PROJECT_COMPARISON.md"]
 p.write_text(json.dumps(d))
CASES.append(("active-uses-revalidation-required", mutate_active_uses_stale_evidence, "active decision relies on revalidation-required evidence"))

def mutate_feature_template_opens_early(r):
 p=r/"v2/gates/features/TEMPLATE.json"; d=json.loads(p.read_text()); d["stage"]="IMPLEMENTATION_ENABLED"; d["impact_checked"]=True; p.write_text(json.dumps(d))
CASES.append(("feature-template-opens-early", mutate_feature_template_opens_early, "feature gate template is not fail-closed"))

def mutate_feature_template_field_drift(r):
 p=r/"v2/gates/features/TEMPLATE.json"; d=json.loads(p.read_text()); d.pop("device_checks"); p.write_text(json.dumps(d))

def mutate_feature_template_device_check_drift(root):
 p=root/"v2/gates/features/TEMPLATE.json"
 d=json.loads(p.read_text()); d["device_checks"]=["legacy free text"]; p.write_text(json.dumps(d))
CASES.append(("feature-template-field-drift", mutate_feature_template_field_drift, "feature gate template fields drifted"))

def mutate_apk_template_opens_early(root):
 p=root/"v2/gates/apk_evidence/TEMPLATE.json"
 d=json.loads(p.read_text()); d["status"]="VERIFIED"; p.write_text(json.dumps(d))

def mutate_apk_template_check_drift(root):
 p=root/"v2/gates/apk_evidence/TEMPLATE.json"
 d=json.loads(p.read_text()); d["apk_checks"]=["legacy free text"]; p.write_text(json.dumps(d))
CASES.append(("feature-template-device-check-drift", mutate_feature_template_device_check_drift, "feature gate template device check contract drifted"))
CASES.append(("apk-template-opens-early", mutate_apk_template_opens_early, "APK evidence template is not fail-closed"))

def mutate_device_template_opens_early(root):
 p=root/"v2/gates/device_evidence/TEMPLATE.json"
 d=json.loads(p.read_text()); d["status"]="ACCEPTED"; p.write_text(json.dumps(d))

def mutate_device_template_check_drift(root):
 p=root/"v2/gates/device_evidence/TEMPLATE.json"
 d=json.loads(p.read_text()); d["checks"]=["legacy free text"]; p.write_text(json.dumps(d))

def mutate_device_template_target_drift(root):
 p=root/"v2/gates/device_evidence/TEMPLATE.json"
 d=json.loads(p.read_text()); d["device"]="OTHER"; p.write_text(json.dumps(d))
CASES.append(("apk-template-check-drift", mutate_apk_template_check_drift, "APK evidence template check contract drifted"))
CASES.append(("device-template-opens-early", mutate_device_template_opens_early, "device evidence template is not fail-closed"))
CASES.append(("device-template-check-drift", mutate_device_template_check_drift, "device evidence template check contract drifted"))
CASES.append(("device-template-target-drift", mutate_device_template_target_drift, "device evidence template is not fail-closed"))

def mutate_domain_policy_invalid_kind(r):
 p=r/"v2/gates/domain_verification_policy.json"; d=json.loads(p.read_text()); d["rules"]["renderer"]=["source","wishful-check"]; p.write_text(json.dumps(d))
CASES.append(("domain-policy-invalid-kind", mutate_domain_policy_invalid_kind, "domain verification policy has invalid kinds"))

def mutate_domain_policy_empty_rules(r):
 p=r/"v2/gates/domain_verification_policy.json"; d=json.loads(p.read_text()); d["rules"]={}; p.write_text(json.dumps(d))
CASES.append(("domain-policy-empty-rules", mutate_domain_policy_empty_rules, "domain verification policy invalid"))

def mutate_dispatch_workflow_bypass(r):
 p=r/".github/workflows/dispatch-bypass-fixture.yml"
 p.write_text("""name: bypass fixture
on:
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: ./gradlew app:assembleWebRelease
""")
CASES.append(("dispatch-workflow-bypass", mutate_dispatch_workflow_bypass, "V2 build workflow bypasses feature gate"))

def mutate_post_gate_control_checkout(r):
 p=r/".github/workflows/build_cb6_v2_signals.yml"; s=p.read_text()
 token="python3 v2/gates/verify_project_gate.py --require-feature-build --feature=signals"
 s=s.replace(token,token+"\n      - name: Replace gated control repo\n        uses: actions/checkout@v4",1)
 p.write_text(s)
CASES.append(("post-gate-control-checkout", mutate_post_gate_control_checkout, "control repo can change after feature gate"))

def mutate_post_gate_control_reset(r):
 p=r/".github/workflows/build_cb6_v2_signals.yml"; s=p.read_text()
 token="python3 v2/gates/verify_project_gate.py --require-feature-build --feature=signals"
 s=s.replace(token,token+"\n          git reset --hard HEAD~1",1)
 p.write_text(s)
CASES.append(("post-gate-control-reset", mutate_post_gate_control_reset, "control repo can change after feature gate"))

def mutate_missing_stamp_in_implementation(r):
 mutate_implementation_with_unverified_upload(r)
 for wf in (r/".github/workflows").glob("*.yml"):
  s=wf.read_text().replace("          python3 v2/gates/create_gate_stamp.py\n","").replace("          python3 v2/gates/create_gate_stamp.py --verify\n",""); wf.write_text(s)
CASES.append(("implementation-missing-gate-stamp", mutate_missing_stamp_in_implementation, "build workflow lacks post-gate control stamp enforcement"))

def test_ci_sha_mismatch():
 env=os.environ.copy(); env["GITHUB_SHA"]="0"*40
 cp=subprocess.run([sys.executable,str(ROOT/"v2/gates/verify_project_gate.py")],cwd=ROOT,text=True,capture_output=True,env=env)
 if cp.returncode==0 or "CI control repo HEAD does not match GITHUB_SHA" not in cp.stdout+cp.stderr:
  raise SystemExit("DESTRUCTIVE TEST FAIL ci-sha-mismatch: "+cp.stdout+cp.stderr)
 print("PASS expected rejection: ci-sha-mismatch -> CI control repo HEAD does not match GITHUB_SHA")

def mutate_workflow_sha_override(r):
 p=r/".github/workflows/build_cb6_v2_signals.yml"; s=p.read_text()
 s=s.replace('SKIP_MAP_DOWNLOAD: "true"','SKIP_MAP_DOWNLOAD: "true"\n      GITHUB_SHA: "0000000000000000000000000000000000000000"',1)
 p.write_text(s)
CASES.append(("workflow-sha-override", mutate_workflow_sha_override, "build workflow overrides GITHUB_SHA"))

def mutate_traceability_stage_mismatch(r):
 p=r/"v2/gates/traceability.json"; d=json.loads(p.read_text())
 d["stage"]="IMPLEMENTATION_ENABLED" if d.get("stage")!="IMPLEMENTATION_ENABLED" else "OVERALL_DESIGN_REBUILD"
 p.write_text(json.dumps(d))

def mutate_implementation_with_unverified_upload(r):
 p=r/"v2/gates/project_state.json"; d=json.loads(p.read_text()); d["stage"]="IMPLEMENTATION_ENABLED"; p.write_text(json.dumps(d))
 for rel in ("v2/gates/traceability.json","v2/gates/authority_policy.json","v2/gates/evidence_inventory.json"):
  q=r/rel; x=json.loads(q.read_text()); x["stage"]="IMPLEMENTATION_ENABLED"; q.write_text(json.dumps(x))
 m=r/"v2/gates/development_method_contract.json"; md=json.loads(m.read_text()); md["stage"]="IMPLEMENTATION_ENABLED"; m.write_text(json.dumps(md))
 t=r/"v2/gates/traceability.json"; td=json.loads(t.read_text()); active=json.loads((r/"v2/gates/active_decisions.json").read_text())["decisions"]
 active_ids={x["id"] for x in active if x.get("status")=="active"}
 for x in td["traces"]:
  if x["decision_id"] in active_ids: x.update({"state":"consumed","design_ref":"docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md","verification":["v2/tests/test_gate_fail_closed.py"]})
 t.write_text(json.dumps(td))
 for wf in (r/".github/workflows").glob("*.yml"):
  s=wf.read_text()
  if "verify_project_gate.py --require-feature-build --feature=" in s:
   token="verify_project_gate.py --require-feature-build --feature="
   pos=s.find(token); end=s.find("\n",pos)
   s=s[:end+1]+"          python3 v2/gates/create_gate_stamp.py\n          python3 v2/gates/create_gate_stamp.py --verify\n"+s[end+1:]
   wf.write_text(s)
CASES.append(("traceability-stage-mismatch", mutate_traceability_stage_mismatch, "traceability stage/schema mismatch"))

def mutate_upstream_lock_commit(r):
 p=r/"v2/gates/upstream_lock.json"; d=json.loads(p.read_text()); d["commit"]="a"*40; p.write_text(json.dumps(d))
CASES.append(("unverified-apk-upload", mutate_implementation_with_unverified_upload, "APK artifact upload is not preceded by APK evidence verification"))

def mutate_development_gate_omits_test(r):
 p=r/".github/workflows/cb6_development_gate.yml"; s=p.read_text(); s=s.replace("python3 v2/tests/test_final_acceptance_fail_closed.py","echo omitted"); p.write_text(s)

def mutate_upstream_head_assertion_removed(r):
 p=r/".github/workflows/build_cb6_v2_signals.yml"; s=p.read_text(); s=s.replace('          test "$(git -C comaps rev-parse HEAD)" = "7113ccb5f086183f8884b2aa4e58c987466b6704"\n',''); p.write_text(s)
CASES.append(("upstream-lock-drift", mutate_upstream_lock_commit, "build workflow does not enforce pinned CoMaps checkout"))
CASES.append(("upstream-head-assertion-removed", mutate_upstream_head_assertion_removed, "build workflow does not enforce pinned CoMaps checkout"))
CASES.append(("development-gate-omits-test", mutate_development_gate_omits_test, "development gate omits required regression test"))


for name,mutate,needle in CASES:
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo"
  shutil.copytree(SRC,root,ignore=shutil.ignore_patterns(".git","out","comaps"))
  mutate(root)
  cp=subprocess.run(["python3","v2/gates/verify_project_integrity.py"],cwd=root,text=True,capture_output=True)
  output=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in output:
   raise SystemExit(f"DESTRUCTIVE TEST FAIL {name}: rc={cp.returncode}\n{output}")
  print("PASS expected rejection:",name,"->",needle)
def mutate_canonical_to_retired_design(r):
 p=r/"v2/gates/project_state.json"; d=json.loads(p.read_text())
 d["stage"]="IMPLEMENTATION_ENABLED"; d["feature_builds_allowed"]=True; d["design_verified"]=True
 d["canonical_design"]="docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md"; p.write_text(json.dumps(d))
 for rel in ("v2/gates/authority_policy.json","v2/gates/evidence_inventory.json","v2/gates/traceability.json"):
  q=r/rel; x=json.loads(q.read_text()); x["stage"]="IMPLEMENTATION_ENABLED"; q.write_text(json.dumps(x))
 m=r/"v2/gates/development_method_contract.json"; md=json.loads(m.read_text()); md["stage"]="IMPLEMENTATION_ENABLED"; m.write_text(json.dumps(md))
 t=r/"v2/gates/traceability.json"; td=json.loads(t.read_text())
 active=json.loads((r/"v2/gates/active_decisions.json").read_text())["decisions"]
 for x in td["traces"]:
  if any(a["id"]==x["decision_id"] and a["status"]=="active" for a in active):
   x.update({"state":"consumed","design_ref":"docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md","verification":["fixture"]})
 t.write_text(json.dumps(td))
 for wf in (r/".github/workflows").glob("*.yml"):
  s=wf.read_text()
  if "verify_project_gate.py --require-feature-build --feature=" in s and "create_gate_stamp.py" not in s:
   token="verify_project_gate.py --require-feature-build --feature="; pos=s.find(token); end=s.find("\n",pos); s=s[:end+1]+"          python3 v2/gates/create_gate_stamp.py\n          python3 v2/gates/create_gate_stamp.py --verify\n"+s[end+1:]
  if "actions/upload-artifact@" in s and "verify_apk_evidence.py" not in s:
   s=s.replace("actions/upload-artifact@","verify_apk_evidence.py # fixture ordering proof\n      - uses: actions/upload-artifact@",1)
  wf.write_text(s)


def test_canonical_retired_project_gate():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns(".git","out","comaps"))
  mutate_canonical_to_retired_design(root)
  env=os.environ.copy(); env.pop("GITHUB_SHA",None)
  cp=subprocess.run(["python3","v2/gates/verify_project_gate.py"],cwd=root,text=True,capture_output=True,env=env)
  out=cp.stdout+cp.stderr
  if cp.returncode==0 or "canonical design" not in out: raise SystemExit("DESTRUCTIVE TEST FAIL canonical-retired-design: "+out)
  print("PASS expected rejection: canonical-retired-design -> canonical design")

test_canonical_retired_project_gate()
print("PASS all destructive integrity cases rejected")
