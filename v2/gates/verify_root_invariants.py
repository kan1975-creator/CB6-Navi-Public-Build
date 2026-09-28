#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(m):
    print("CB6 ROOT INVARIANT FAIL:",m); raise SystemExit(1)
root=json.loads((ROOT/"v2/gates/root_invariants.json").read_text(encoding="utf-8"))
manifest=json.loads((ROOT/"v2/gates/repository_state_manifest.json").read_text(encoding="utf-8"))
if root.get("status")!="ROOT_INVARIANT": fail("root invariant authority missing")
cert=root.get("certification",{})
if cert.get("status") not in {"UNDER_CONSTRUCTION","CERTIFIED"}: fail("root certification state invalid")
if cert.get("status")=="UNDER_CONSTRUCTION" and cert.get("feature_execution_permitted") is not False: fail("lower layers must be blocked while root is under construction")
if cert.get("status")=="CERTIFIED":
    if cert.get("feature_execution_permitted") is not True: fail("certified root execution state inconsistent")
    proof=cert.get("proof",{})
    required={"context_loss","missing_state","permission_fail_closed","repository_reconstruction","historical_incidents","unknown_change","independent_verification","extensibility","artifact_identity","device_evidence","zero_omission"}
    if set(proof)!=required or not all(v is True for v in proof.values()): fail("root certification proof incomplete")
inv=root.get("non_negotiable_invariants",{})
if not inv or not all(v is True for v in inv.values()): fail("root invariant weakened")
required=root.get("required_reconstruction_outputs",[])
outputs=manifest.get("outputs",{})
if set(outputs)!=set(required): fail("reconstruction outputs mismatch")
for name,paths in outputs.items():
    if not isinstance(paths,list) or not paths: fail("reconstruction output empty: "+name)
    for rel in paths:
        if not isinstance(rel,str) or not rel or not (ROOT/rel).is_file(): fail("reconstruction path missing: "+str(rel))
        if "chat" in rel.lower() or "conversation" in rel.lower(): fail("chat dependency in reconstruction: "+rel)
# Cross-file stage/permission consistency is part of Root, not metadata hygiene.
project=json.loads((ROOT/"v2/gates/project_state.json").read_text(encoding="utf-8"))
authority=json.loads((ROOT/"v2/gates/authority_policy.json").read_text(encoding="utf-8"))
evidence=json.loads((ROOT/"v2/gates/evidence_inventory.json").read_text(encoding="utf-8"))
method=json.loads((ROOT/"v2/gates/development_method_completion.json").read_text(encoding="utf-8"))
if project.get("feature_builds_allowed") is not True:
    if authority.get("stage")=="IMPLEMENTATION_ENABLED": fail("authority stage contradicts project feature-build lock")
    if evidence.get("stage")=="IMPLEMENTATION_ENABLED": fail("evidence stage contradicts project feature-build lock")
if project.get("stage")=="OVERALL_DESIGN_REBUILD" and project.get("design_verified") is not False:
    fail("design rebuild cannot be marked verified")
trace=json.loads((ROOT/"v2/gates/traceability.json").read_text(encoding="utf-8"))
if trace.get("stage")!=project.get("stage"):
    fail("traceability stage contradicts project stage")
contract=json.loads((ROOT/"v2/gates/development_method_contract.json").read_text(encoding="utf-8"))
if contract.get("stage")!=project.get("stage"):
    fail("development method contract stage contradicts project stage")
if method.get("status")!="COMPLETE" and project.get("feature_builds_allowed") is True:
    fail("feature builds cannot be enabled while method completion is not COMPLETE")
inc=json.loads((ROOT/"v2/gates/historical_incidents.json").read_text(encoding="utf-8"))
if inc.get("status")!="ACTIVE" or not inc.get("incidents"): fail("historical incident corpus missing")
ids=[x.get("id") for x in inc["incidents"]]
if None in ids or len(ids)!=len(set(ids)): fail("historical incident ids invalid")
for x in inc["incidents"]:
    proof=x.get("proof","")
    if not proof or not (ROOT/proof).is_file() or not x.get("cause") or not x.get("expected_block"): fail("historical incident proof incomplete: "+str(x.get("id")))
print("CB6 ROOT INVARIANT PASS: repository-only state is reconstructable")
