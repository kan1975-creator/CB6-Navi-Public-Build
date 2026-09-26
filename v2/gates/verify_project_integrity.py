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
spec=load("v2/gates/current_spec.json")
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

# Machine-readable current specification must be internally complete.
sig=spec.get("signal",{})
disp=sig.get("display",{})
acq=sig.get("acquisition",{})
if not disp.get("symbols") or not disp.get("zoom_symbols"): fail("signal display spec incomplete")
if set(disp.get("zoom_symbols",{})) & set(disp.get("forward_zoom_symbols",{})): fail("signal zoom ownership overlaps")
used=set(disp.get("zoom_symbols",{}).values()) | set(disp.get("forward_zoom_symbols",{}).values())
if not used <= set(disp["symbols"]): fail("signal zoom references undeclared symbol")
for k in ("radius_m","max_points","refresh_ms","retry_ms","movement_m","forward_max_m","forward_cone_deg","cache_max_ms","osm_queries"):
 if k not in acq: fail("signal acquisition spec missing "+k)
# Audits must consume current_spec rather than hard-code current display mapping.
audit=(ROOT/"v2/audits/audit_signals.py").read_text(encoding="utf-8")
if "gates/current_spec.json" not in audit: fail("signal audit does not consume current_spec")
for stale in ('[(14,\'xs\'), (15,\'xs\'), (17,\'m\'), (19,\'l\')]',):
 if stale in audit: fail("signal audit duplicates current symbol mapping")

# Retired overall design may not silently become canonical.
ret=(ROOT/state["retired_design"]).read_text(encoding="utf-8")
if "RETIRED AS CANONICAL" not in ret: fail("retired design lost retirement marker")
print(f"CB6 INTEGRITY PASS: {len(active)} active decisions traced; V2 workflow bypass scan clean")
