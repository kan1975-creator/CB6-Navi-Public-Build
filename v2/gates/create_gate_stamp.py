#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"out/gate_stamp.json"
CONTROL=["v2/gates/project_state.json","v2/gates/active_decisions.json","v2/gates/traceability.json","v2/gates/authority_policy.json","v2/gates/evidence_inventory.json","v2/gates/current_spec.json","v2/gates/domain_verification_policy.json","v2/gates/upstream_lock.json"]
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
if "--verify" in sys.argv:
 if not OUT.is_file(): raise SystemExit("CB6 GATE STAMP FAIL: stamp missing")
 d=json.loads(OUT.read_text())
 if set(d)!={"schema","files"} or d["schema"]!=1 or set(d["files"])!=set(CONTROL): raise SystemExit("CB6 GATE STAMP FAIL: stamp contract invalid")
 for p in CONTROL:
  if not (ROOT/p).is_file() or sha(p)!=d["files"][p]: raise SystemExit("CB6 GATE STAMP FAIL: control file changed after gate: "+p)
 print("CB6 GATE STAMP PASS")
else:
 OUT.parent.mkdir(exist_ok=True)
 OUT.write_text(json.dumps({"schema":1,"files":{p:sha(p) for p in CONTROL}},indent=2)+"\n")
 print("CB6 GATE STAMP CREATED")
