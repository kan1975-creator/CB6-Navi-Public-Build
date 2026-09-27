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
if cert.get("status")=="CERTIFIED" and cert.get("feature_execution_permitted") is not True: fail("certified root execution state inconsistent")
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
inc=json.loads((ROOT/"v2/gates/historical_incidents.json").read_text(encoding="utf-8"))
if inc.get("status")!="ACTIVE" or not inc.get("incidents"): fail("historical incident corpus missing")
ids=[x.get("id") for x in inc["incidents"]]
if None in ids or len(ids)!=len(set(ids)): fail("historical incident ids invalid")
for x in inc["incidents"]:
    proof=x.get("proof","")
    if not proof or not (ROOT/proof).is_file() or not x.get("cause") or not x.get("expected_block"): fail("historical incident proof incomplete: "+str(x.get("id")))
print("CB6 ROOT INVARIANT PASS: repository-only state is reconstructable")
