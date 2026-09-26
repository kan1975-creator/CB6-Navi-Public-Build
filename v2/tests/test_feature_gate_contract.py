#!/usr/bin/env python3
"""Destructive tests for the generic per-feature implementation contract."""
import json, shutil, subprocess, tempfile, os
from pathlib import Path
SRC=Path(__file__).resolve().parents[2]

def run_case(name, mutate, needle):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo"; shutil.copytree(SRC,root,ignore=shutil.ignore_patterns(".git","out","comaps"))
  state=root/"v2/gates/project_state.json"; d=json.loads(state.read_text())
  d.update({"stage":"IMPLEMENTATION_ENABLED","feature_builds_allowed":True,"design_verified":True,"canonical_design":"docs/CB6_DEVELOPMENT_EXECUTION_GATE.md"})
  state.write_text(json.dumps(d))
  # Keep all stage-coupled gate inputs coherent so each case reaches the
  # per-feature contract under test rather than failing the global integrity lock.
  for rel in ("v2/gates/authority_policy.json","v2/gates/evidence_inventory.json"):
   p=root/rel; x=json.loads(p.read_text()); x["stage"]="IMPLEMENTATION_ENABLED"; p.write_text(json.dumps(x))
  trace=root/"v2/gates/traceability.json"; t=json.loads(trace.read_text()); t["stage"]="IMPLEMENTATION_ENABLED"
  for x in t["traces"]:
   if x["decision_id"]=="SIG-200M-001": x.update({"state":"consumed","design_ref":"docs/CB6_DEVELOPMENT_EXECUTION_GATE.md","verification":["fixture"]})
  # This test isolates feature-contract behavior: all active requirements must be consumed for implementation stage.
  active=json.loads((root/"v2/gates/active_decisions.json").read_text())["decisions"]
  for x in t["traces"]:
   if any(a["id"]==x["decision_id"] and a["status"]=="active" for a in active):
    x.update({"state":"consumed","design_ref":"docs/CB6_DEVELOPMENT_EXECUTION_GATE.md","verification":["fixture"]})
  trace.write_text(json.dumps(t))
  gate=root/"v2/gates/features/testfeature.json"; gate.parent.mkdir(exist_ok=True)
  f={"schema":1,"feature_id":"testfeature","requirements":["SIG-200M-001"],"affected_domains":["signals","renderer","symbols","audits","tests"],"domain_verification":{"signals":["v2/signals"],"renderer":["v2/signals","v2/audits/audit_signals.py","v2/tests/test_gate_fail_closed.py"],"symbols":["v2/signals","v2/audits/audit_signals.py"],"audits":["v2/audits/audit_signals.py"],"tests":["v2/tests/test_gate_fail_closed.py"]},"design_section":"signals/display","impact_checked":True,"impact_record":"v2/gates/impact_records/testfeature.json","repo_sweep_required":True,"source_paths":["v2/signals"],"audits":["v2/audits/audit_signals.py"],"tests":["v2/tests/test_gate_fail_closed.py"],"apk_checks":["verify active resources from current_spec"],"device_checks":[{"id":"cb6-acceptance","description":"CB6 real-device acceptance required"}],"device_evidence":"PENDING","stage":"IMPLEMENTATION_ENABLED"}
  impact=root/"v2/gates/impact_records/testfeature.json"; impact.parent.mkdir(exist_ok=True)
  impact.write_text(json.dumps({"schema":1,"feature_id":f["feature_id"],"requirements":f["requirements"],"affected_domains":f["affected_domains"],"reviewed_paths":["docs/CB6_CHANGE_IMPACT_MAP.md"]}))
  mutate(f)
  if not name.startswith("impact-record-"):
   impact.write_text(json.dumps({"schema":1,"feature_id":f.get("feature_id"),"requirements":f.get("requirements",[]),"affected_domains":f.get("affected_domains",[]),"reviewed_paths":["docs/CB6_CHANGE_IMPACT_MAP.md"]}))
  gate.write_text(json.dumps(f))
  if name=="impact-record-requirements-mismatch":
   x=json.loads(impact.read_text()); x["requirements"]=["DOES-NOT-EXIST"]; impact.write_text(json.dumps(x))
  if name=="impact-record-domains-mismatch":
   x=json.loads(impact.read_text()); x["affected_domains"]=["signals"]; impact.write_text(json.dumps(x))
  if name=="impact-record-reviewed-path-missing":
   x=json.loads(impact.read_text()); x["reviewed_paths"]=["docs/DOES_NOT_EXIST.md"]; impact.write_text(json.dumps(x))
  if name=="impact-record-field-drift":
   x=json.loads(impact.read_text()); x["unreviewed_note"]="bypass"; impact.write_text(json.dumps(x))
  if name=="impact-record-missing": impact.unlink()
  env=os.environ.copy(); env.pop("GITHUB_SHA",None)
  cp=subprocess.run(["python3","v2/gates/verify_project_gate.py","--require-feature-build","--feature=testfeature"],cwd=root,text=True,capture_output=True,env=env)
  out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(f"FEATURE CONTRACT TEST FAIL {name}: rc={cp.returncode}\n{out}")
  print("PASS expected feature rejection:",name,"->",needle)

cases=[
 ("missing-requirements",lambda f:f.pop("requirements"),"feature gate fields missing"),
 ("unknown-requirement",lambda f:f.__setitem__("requirements",["DOES-NOT-EXIST"]),"non-active requirements"),
 ("missing-affected-domains",lambda f:f.__setitem__("affected_domains",[]),"affected_domains not declared"),
 ("incomplete-affected-domains",lambda f:f.__setitem__("affected_domains",["signals"]),"omits affected domains"),
 ("missing-domain-verification",lambda f:f.__setitem__("domain_verification",{}),"domains lack verification"),
 ("unknown-domain-verification-path",lambda f:f["domain_verification"].__setitem__("renderer",["v2/not-declared"]),"domain verification uses undeclared paths"),
 ("renderer-source-only",lambda f:f["domain_verification"].__setitem__("renderer",["v2/signals"]),"domain lacks required verification kind"),
 ("impact-record-missing",lambda f:None,"feature impact record missing"),
 ("impact-record-requirements-mismatch",lambda f:None,"feature impact record requirements mismatch"),
 ("impact-record-domains-mismatch",lambda f:None,"feature impact record domains mismatch"),
 ("impact-record-reviewed-path-missing",lambda f:None,"feature impact reviewed path missing"),
 ("impact-record-field-drift",lambda f:None,"feature impact record fields drifted"),
 ("no-repo-sweep",lambda f:f.__setitem__("repo_sweep_required",False),"repo-wide sweep not required"),
 ("missing-source",lambda f:(f.__setitem__("source_paths",["v2/does-not-exist"]),[f["domain_verification"].__setitem__(d,["v2/does-not-exist","v2/audits/audit_signals.py","v2/tests/test_gate_fail_closed.py"]) for d in ("signals","renderer","symbols")]),"source_paths path missing"),
 ("no-apk-check",lambda f:f.__setitem__("apk_checks",[]),"apk_checks not declared"),
 ("no-device-check",lambda f:f.__setitem__("device_checks",[]),"device_checks must use id/description records"),
 ("premature-device-evidence",lambda f:f.__setitem__("device_evidence","VERIFIED"),"device evidence must remain pending before build"),
]
for c in cases: run_case(*c)
print("PASS generic feature contract destructive cases rejected")
