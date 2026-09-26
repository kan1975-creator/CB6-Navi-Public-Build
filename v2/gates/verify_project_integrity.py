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
authority=load("v2/gates/authority_policy.json")
evidence=load("v2/gates/evidence_inventory.json")
if trace.get("schema")!=1 or trace.get("stage")!=state.get("stage"): fail("traceability stage/schema mismatch")
if evidence.get("schema")!=1 or evidence.get("stage")!=state.get("stage"): fail("evidence inventory stage/schema mismatch")
items=evidence.get("evidence",[])
eids=[x.get("id") for x in items]
epaths=[x.get("path") for x in items]
if not items or None in eids or len(eids)!=len(set(eids)): fail("evidence IDs missing/duplicated")
if None in epaths or len(epaths)!=len(set(epaths)): fail("evidence paths missing/duplicated")
valid_evidence_status={"active","historical","historical-mixed","retired","revalidation-required"}
for x in items:
 for k in ("id","type","path","status"):
  if not x.get(k): fail(f"evidence item missing {k}: {x.get('id')}")
 if x["status"] not in valid_evidence_status: fail("invalid evidence status: "+x["id"])
 if not (ROOT/x["path"]).is_file(): fail("evidence inventory path missing: "+x["path"])
 if x["status"]=="historical-mixed":
  cp=x.get("clause_policy",{})
  if cp.get("state")!="requires-explicit-decision-link" or not cp.get("note"): fail("historical-mixed evidence lacks clause policy: "+x["id"])
 if x["status"]=="revalidation-required":
  rv=x.get("revalidation",{})
  if rv.get("state") not in {"required","validated"}: fail("invalid evidence revalidation state: "+x["id"])
  if rv["state"]=="validated":
   if not rv.get("record") or not (ROOT/rv["record"]).is_file() or not rv.get("verification"): fail("validated evidence lacks revalidation record/verification: "+x["id"])
active_evidence_paths={x["path"] for x in items if x["status"]=="active"}
restricted_evidence_paths={x["path"] for x in items if x["status"]!="active"}
evidence_by_path={x["path"]:x for x in items}
if authority.get("schema")!=1 or authority.get("stage")!=state.get("stage"): fail("authority policy stage/schema mismatch")
for rel in authority.get("current_authorities",[]):
 if not (ROOT/rel).is_file(): fail("current authority missing: "+rel)
for rel in authority.get("historical_docs",[]):
 p=ROOT/rel
 if not p.is_file(): fail("historical authority document missing: "+rel)
 txt=p.read_text(encoding="utf-8")
 for phrase in authority.get("forbidden_historical_authority_phrases",[]):
  if phrase in txt: fail("historical document regained authority: "+rel+" -> "+phrase)
if reg.get("schema")!=1 or trace.get("schema")!=1: fail("unsupported registry schema")
decisions=reg.get("decisions",[])
ids=[d.get("id") for d in decisions]
if None in ids or len(ids)!=len(set(ids)): fail("decision IDs missing/duplicated")
valid_status={"active","superseded","retired"}
for d in decisions:
 if d.get("status") not in valid_status: fail("invalid decision status "+str(d.get("id")))
 for k in ("kind","spec_key","requirement","affected","evidence","acceptance"):
  if not d.get(k): fail(f"{d.get('id')} missing {k}")
# Evidence references are executable integrity inputs, not unchecked prose.
# Every repository evidence path used by a decision must be inventoried, so evidence authority/status cannot bypass the inventory.
inventory_paths={x["path"] for x in items}
for d in decisions:
 for ev in d["evidence"]:
  if ev.startswith(("docs/","v2/","AGENTS.md")):
   if not (ROOT/ev).is_file(): fail(f"{d['id']} evidence path missing: {ev}")
   if ev not in inventory_paths: fail(f"{d['id']} evidence absent from inventory: {ev}")
   if d["status"]=="active" and evidence_by_path[ev]["status"]=="retired": fail(f"{d['id']} active decision relies directly on retired evidence: {ev}")
   if d["status"]=="active" and evidence_by_path[ev]["status"]=="revalidation-required": fail(f"{d['id']} active decision relies on revalidation-required evidence: {ev}")
   if d["status"]=="active" and evidence_by_path[ev]["status"]=="historical-mixed":
    sc=d.get("evidence_scopes",{}).get(ev,{})
    if not sc.get("scope") or not sc.get("supersession"): fail(f"{d['id']} historical-mixed evidence lacks requirement scope: {ev}")

# One current owner per single-valued specification key; supersession must be reciprocal.
active_by_key={}
by_id={d["id"]:d for d in decisions}
for d in decisions:
 if d["status"]=="active":
  key=d["spec_key"]
  if key in active_by_key: fail(f"multiple active owners for spec_key {key}: {active_by_key[key]},{d['id']}")
  active_by_key[key]=d["id"]
 for old in d.get("supersedes",[]):
  if old not in by_id: fail(f"{d['id']} supersedes unknown decision: {old}")
  if by_id[old]["status"]!="superseded" or by_id[old].get("superseded_by")!=d["id"]:
   fail(f"non-reciprocal supersession: {d['id']} -> {old}")
 if d["status"]=="superseded":
  newer=d.get("superseded_by")
  if not newer or newer not in by_id or by_id[newer]["status"]!="active" or d["id"] not in by_id[newer].get("supersedes",[]):
   fail(f"superseded decision lacks active reciprocal replacement: {d['id']}")

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
  for ev in d["evidence"]:
   if ev in restricted_evidence_paths and not t.get("verification"):
    fail("consumed decision relies on restricted evidence without verification: "+d["id"])
  ref=t.get("design_ref","")
  if not ref or not (ROOT/ref).is_file(): fail("consumed decision lacks valid design ref: "+d["id"])
  if not t.get("verification"): fail("consumed decision lacks verification: "+d["id"])
if state["stage"]=="IMPLEMENTATION_ENABLED":
 pending=[t["decision_id"] for t in traces if t["decision_id"] in active and t["state"]!="consumed"]
 if pending: fail("implementation enabled with unconsumed active decisions: "+",".join(sorted(pending)))

domain_policy=load("v2/gates/domain_verification_policy.json")
if domain_policy.get("schema")!=1 or not isinstance(domain_policy.get("rules"),dict) or not domain_policy["rules"] or not domain_policy.get("default_required_kinds"):
 fail("domain verification policy invalid")
valid_kinds={"source","audit","test","device"}
for domain,kinds in domain_policy["rules"].items():
 if not isinstance(kinds,list) or not kinds or set(kinds)-valid_kinds: fail("domain verification policy has invalid kinds: "+domain)

# Feature-gate template is part of the development method and must remain fail-closed.
template=load("v2/gates/features/TEMPLATE.json")
required_feature_fields={"schema","feature_id","requirements","affected_domains","domain_verification","design_section","impact_checked","impact_record","repo_sweep_required","source_paths","audits","tests","apk_checks","device_checks","device_evidence","stage"}
if set(template) != required_feature_fields: fail("feature gate template fields drifted")
if template.get("schema")!=1 or template.get("impact_checked") is not False or template.get("repo_sweep_required") is not True or template.get("device_evidence")!="PENDING" or template.get("stage")!="DESIGN":
 fail("feature gate template is not fail-closed")
tdc=template.get("device_checks")
if not isinstance(tdc,list) or len(tdc)!=1 or not isinstance(tdc[0],dict) or set(tdc[0])!={"id","description"} or tdc[0].get("id")!="REPLACE_WITH_CHECK_ID" or tdc[0].get("description")!="REPLACE_WITH_EXPLICIT_CB6_REAL_DEVICE_ACCEPTANCE":
 fail("feature gate template device check contract drifted")

# Any workflow that can run on cb6-v2-clean and can build must fail closed through the gate.
wfdir=ROOT/".github/workflows"
for p in sorted(list(wfdir.glob("*.yml"))+list(wfdir.glob("*.yaml"))):
 s=p.read_text(encoding="utf-8")
 if p.name=="cb6_development_gate.yml": continue
 # Branch-name matching is not sufficient: a workflow_dispatch build can be
 # manually run from cb6-v2-clean even when its push branches are legacy-only.
 dispatchable=bool(re.search(r"(?m)^\s*workflow_dispatch\s*:",s))
 targets_v2="cb6-v2-clean" in s or dispatchable
 if not targets_v2: continue
 buildish=bool(re.search(r"(gradlew|assemble|apply_identity\.py|apply_signals\.py)",s))
 if buildish:
  # GitHub owns GITHUB_SHA. Build workflows must not shadow, clear or rewrite it.
  if any(line.strip().startswith("GITHUB_SHA:") or line.strip().startswith("GITHUB_SHA=") for line in s.splitlines()) or "unset GITHUB_SHA" in s:
   fail("build workflow overrides GITHUB_SHA: "+p.name)
  token="verify_project_gate.py --require-feature-build --feature="
  if token not in s: fail("V2 build workflow bypasses feature gate: "+p.name)
  if s.index(token)>min([i for i in [s.find("gradlew"),s.find("apply_identity.py"),s.find("apply_signals.py")] if i>=0]):
   fail("feature gate occurs after build/transform work: "+p.name)
  gate_pos=s.index(token)
  post_gate=s[gate_pos:]
  # After the control repository has been gated, do not replace/reset it. Commands
  # explicitly scoped to the separate comaps/ checkout are allowed.
  dangerous=[]
  for line in post_gate.splitlines():
   stripped=line.strip()
   if "uses:" in stripped and "actions/checkout@" in stripped: dangerous.append(stripped)
   parts=stripped.split()
   if len(parts)>=2 and parts[0]=="git" and parts[1] in {"checkout","reset","switch","pull","fetch"}: dangerous.append(stripped)
  if dangerous: fail("control repo can change after feature gate: "+p.name+" -> "+" | ".join(dangerous))

# APK-evidence template is part of the development method and must remain fail-closed.
apk_template=load("v2/gates/apk_evidence/TEMPLATE.json")
required_apk_template_fields={"schema","feature_id","build_commit","feature_gate","apk_path","apk_sha256","apk_checks","status"}
if set(apk_template)!=required_apk_template_fields: fail("APK evidence template fields drifted")
if apk_template.get("schema")!=1 or apk_template.get("status")!="PENDING": fail("APK evidence template is not fail-closed")
atc=apk_template.get("apk_checks")
if not isinstance(atc,list) or len(atc)!=1 or not isinstance(atc[0],dict) or set(atc[0])!={"id","result","evidence"} or atc[0].get("id")!="REPLACE_WITH_APK_CHECK_ID" or atc[0].get("result")!="PENDING" or atc[0].get("evidence")!="REPLACE_ME":
 fail("APK evidence template check contract drifted")

# Device-evidence template is part of the development method and must remain fail-closed.
device_template=load("v2/gates/device_evidence/TEMPLATE.json")
required_device_template_fields={"schema","feature_id","build_commit","feature_gate","apk_evidence","apk_sha256","device","android_version","checks","status"}
if set(device_template)!=required_device_template_fields: fail("device evidence template fields drifted")
if device_template.get("schema")!=1 or device_template.get("status")!="PENDING" or device_template.get("device")!="CB6" or device_template.get("android_version")!="13": fail("device evidence template is not fail-closed")
dtc=device_template.get("checks")
if not isinstance(dtc,list) or len(dtc)!=1 or not isinstance(dtc[0],dict) or set(dtc[0])!={"id","result","evidence"} or dtc[0].get("id")!="REPLACE_ME" or dtc[0].get("result")!="PENDING" or dtc[0].get("evidence")!="REPLACE_ME":
 fail("device evidence template check contract drifted")

# APK artifacts may never be published before APK evidence verification once implementation is enabled.
if state.get("stage")=="IMPLEMENTATION_ENABLED":
 for p in workflows:
  s=p.read_text(encoding="utf-8")
  upload=s.find("actions/upload-artifact@")
  if upload<0: continue
  verify=s.find("verify_apk_evidence.py")
  if verify<0 or verify>upload: fail("APK artifact upload is not preceded by APK evidence verification: "+p.name)

# All build workflows must consume the single pinned CoMaps authority.
upstream=load("v2/gates/upstream_lock.json")
if set(upstream)!={"schema","upstream","repository","commit","policy"} or upstream.get("schema")!=1 or upstream.get("upstream")!="CoMaps" or upstream.get("policy")!="exact": fail("upstream lock invalid")
pinned=upstream.get("commit","")
if len(pinned)!=40 or any(ch not in "0123456789abcdef" for ch in pinned): fail("upstream lock commit invalid")
for p in workflows:
 s=p.read_text(encoding="utf-8")
 if "git -C comaps fetch" in s and pinned not in s: fail("build workflow does not use pinned CoMaps commit: "+p.name)

# Machine-readable current specification must be internally complete.
sig=spec.get("signal",{})
disp=sig.get("display",{})
acq=sig.get("acquisition",{})
if not disp.get("zoom_symbols") or not disp.get("svg_dimensions"): fail("signal display spec incomplete")
if set(disp.get("zoom_symbols",{})) & set(disp.get("forward_zoom_symbols",{})): fail("signal zoom ownership overlaps")
used=set(disp.get("zoom_symbols",{}).values()) | set(disp.get("forward_zoom_symbols",{}).values())
if not used <= set(disp["svg_dimensions"]): fail("signal zoom references symbol without dimensions")
for k in ("radius_m","max_points","refresh_ms","retry_ms","movement_m","forward_max_m","forward_cone_deg","cache_max_ms","osm_queries"):
 if k not in acq: fail("signal acquisition spec missing "+k)
# Audits must consume current_spec rather than hard-code current display mapping.
audit=(ROOT/"v2/audits/audit_signals.py").read_text(encoding="utf-8")
if "gates/current_spec.json" not in audit: fail("signal audit does not consume current_spec")
for stale in ('[(14,\'xs\'), (15,\'xs\'), (17,\'m\'), (19,\'l\')]', "spec['display']['symbols']"):
 if stale in audit: fail("signal audit duplicates or requires historical resource inventory")

# Retired overall design may not silently become canonical.
ret=(ROOT/state["retired_design"]).read_text(encoding="utf-8")
if "RETIRED AS CANONICAL" not in ret: fail("retired design lost retirement marker")
print(f"CB6 INTEGRITY PASS: {len(active)} active decisions traced; V2 workflow bypass scan clean")
