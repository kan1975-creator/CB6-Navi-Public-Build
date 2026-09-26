#!/usr/bin/env python3
"""Repository-wide CB6 V2 structural/traceability gate."""
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(m): raise SystemExit("CB6 INTEGRITY FAIL: "+m)
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))

state=load("v2/gates/project_state.json")
reg=load("v2/gates/active_decisions.json")
trace=load("v2/gates/traceability.json")
if reg.get("schema")!=1 or trace.get("schema")!=1: fail("unsupported registry schema")
decisions=reg.get("decisions",[])
ids=[d.get("id") for d in decisions]
if None in ids or len(ids)!=len(set(ids)): fail("decision IDs missing/duplicated")
valid_status={"active","superseded","retired"}
for d in decisions:
 if d.get("status") not in valid_status: fail("invalid decision status "+str(d.get("id")))
 for k in ("kind","requirement","affected","evidence","acceptance"):
  if not d.get(k): fail(f"{d.get('id')} missing {k}")
traces=trace.get("traces",[])
tids=[t.get("decision_id") for t in traces]
if len(tids)!=len(set(tids)): fail("duplicate trace rows")
active={d["id"] for d in decisions if d["status"]=="active"}
missing=active-set(tids)
if missing: fail("active decisions absent from traceability: "+",".join(sorted(missing)))
unknown=set(tids)-set(ids)
if unknown: fail("trace references unknown decisions: "+",".join(sorted(unknown)))
allowed={"consumed","pending-redesign","superseded"}
for t in traces:
 if t.get("state") not in allowed: fail("invalid trace state "+str(t.get("decision_id")))
 d=next(d for d in decisions if d["id"]==t["decision_id"])
 if d["status"]=="superseded" and t["state"]=="consumed": fail("superseded decision consumed: "+d["id"])
 if t["state"]=="consumed":
  ref=t.get("design_ref","")
  if not ref or not (ROOT/ref).is_file(): fail("consumed decision lacks valid design ref: "+d["id"])
  if not t.get("verification"): fail("consumed decision lacks verification: "+d["id"])
if state["stage"]=="IMPLEMENTATION_ENABLED":
 pending=[t["decision_id"] for t in traces if t["decision_id"] in active and t["state"]!="consumed"]
 if pending: fail("implementation enabled with unconsumed active decisions: "+",".join(sorted(pending)))

# Any workflow that can run on cb6-v2-clean and can build must fail closed through the gate.
wfdir=ROOT/".github/workflows"
for p in sorted(list(wfdir.glob("*.yml"))+list(wfdir.glob("*.yaml"))):
 s=p.read_text(encoding="utf-8")
 if p.name=="cb6_development_gate.yml": continue
 if "cb6-v2-clean" not in s: continue
 buildish=bool(re.search(r"(gradlew|assemble|apply_identity\.py|apply_signals\.py)",s))
 if buildish:
  token="verify_project_gate.py --require-feature-build --feature="
  if token not in s: fail("V2 build workflow bypasses feature gate: "+p.name)
  if s.index(token)>min([i for i in [s.find("gradlew"),s.find("apply_identity.py"),s.find("apply_signals.py")] if i>=0]):
   fail("feature gate occurs after build/transform work: "+p.name)

# Retired overall design may not silently become canonical.
ret=(ROOT/state["retired_design"]).read_text(encoding="utf-8")
if "RETIRED AS CANONICAL" not in ret: fail("retired design lost retirement marker")
print(f"CB6 INTEGRITY PASS: {len(active)} active decisions traced; V2 workflow bypass scan clean")
