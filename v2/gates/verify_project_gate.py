#!/usr/bin/env python3
import json, pathlib, sys, os, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
STATE=ROOT/"v2/gates/project_state.json"
EXEC=ROOT/"docs/CB6_DEVELOPMENT_EXECUTION_GATE.md"
OLD=ROOT/"docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md"
def fail(msg):
 print("CB6 DEVELOPMENT GATE FAIL:",msg); raise SystemExit(1)
for p in (STATE,EXEC,OLD):
 if not p.exists(): fail("required gate input missing: "+str(p.relative_to(ROOT)))
s=json.loads(STATE.read_text(encoding="utf-8"))
# In GitHub Actions the gated control repository must be exactly the workflow commit.
# Local/offline verification remains supported when GITHUB_SHA is absent.
ci_sha=os.environ.get("GITHUB_SHA","").strip()
if ci_sha:
 cp=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True)
 if cp.returncode!=0: fail("cannot resolve control repo HEAD in CI")
 head=cp.stdout.strip()
 if head!=ci_sha: fail("CI control repo HEAD does not match GITHUB_SHA")
if s.get("schema")!=1: fail("unsupported project_state schema")
if s.get("branch")!="cb6-v2-clean": fail("wrong branch authority")
stage=s.get("stage")
if stage not in {"OVERALL_DESIGN_REBUILD","IMPLEMENTATION_ENABLED"}: fail("unknown stage: "+str(stage))
old=OLD.read_text(encoding="utf-8")
if "RETIRED AS CANONICAL" not in old: fail("retired overall design became canonical again")
if stage=="OVERALL_DESIGN_REBUILD":
 if s.get("feature_builds_allowed") is not False: fail("feature builds must be disabled during design rebuild")
 print("CB6 DEVELOPMENT GATE PASS: overall-design rebuild; feature builds BLOCKED")
 if "--require-feature-build" in sys.argv: fail("feature build requested while overall design rebuild is active")
 raise SystemExit(0)
# Implementation enablement must be independently proven by the repository-wide
# integrity gate. Do not trust project_state booleans as sufficient authority.
cp=subprocess.run([sys.executable, str(ROOT/"v2/gates/verify_project_integrity.py")], cwd=ROOT, text=True, capture_output=True)
if cp.returncode != 0:
 fail("implementation enablement lacks integrity proof: "+(cp.stdout+cp.stderr).strip())
canonical=ROOT/s.get("canonical_design","")
if not canonical.is_file(): fail("canonical rebuilt design missing")
if not s.get("design_verified"): fail("rebuilt design not verified")
if s.get("feature_builds_allowed") is not True: fail("feature builds not authorized")
# Feature builds additionally require a per-feature gate record.
if "--require-feature-build" in sys.argv:
 feature=None
 for arg in sys.argv:
  if arg.startswith("--feature="): feature=arg.split("=",1)[1]
 if not feature: fail("feature build requires --feature=<gate-id>")
 fp=ROOT/"v2/gates/features"/(feature+".json")
 if not fp.is_file(): fail("missing per-feature gate record: "+feature)
 f=json.loads(fp.read_text(encoding="utf-8"))
 required={"schema","feature_id","requirements","affected_domains","domain_verification","design_section","impact_checked","repo_sweep_required","source_paths","audits","tests","apk_checks","device_checks","stage"}
 missing=sorted(required-set(f))
 if missing: fail("feature gate fields missing: "+",".join(missing))
 if f.get("schema")!=1 or f.get("feature_id")!=feature: fail("feature gate identity invalid")
 if not f.get("impact_checked"): fail("feature impact check incomplete")
 if f.get("repo_sweep_required") is not True: fail("feature repo-wide sweep not required")
 if f.get("stage")!="IMPLEMENTATION_ENABLED": fail("feature implementation not enabled")
 for key in ("requirements","source_paths","audits","tests","apk_checks","device_checks"):
  if not isinstance(f.get(key),list) or not f[key]: fail("feature gate "+key+" not declared")
 decisions=json.loads((ROOT/"v2/gates/active_decisions.json").read_text(encoding="utf-8")).get("decisions",[])
 active={d["id"] for d in decisions if d.get("status")=="active"}
 active_by_id={d["id"]:d for d in decisions if d.get("status")=="active"}
 unknown=sorted(set(f["requirements"])-active)
 if unknown: fail("feature gate references non-active requirements: "+",".join(unknown))
 # A feature contract must declare the affected domains of every requirement it owns.
 # This prevents a narrow source list from silently ignoring renderer/cache/UI/etc impact.
 declared_domains=set(f.get("affected_domains",[]))
 if not declared_domains: fail("feature gate affected_domains not declared")
 required_domains=set().union(*(set(active_by_id[r].get("affected",[])) for r in f["requirements"]))
 missing_domains=sorted(required_domains-declared_domains)
 if missing_domains: fail("feature gate omits affected domains: "+",".join(missing_domains))
 # Every declared impact domain needs an explicit verification route. A domain name
 # alone is not evidence that its source/regression surface was actually checked.
 dv=f.get("domain_verification")
 if not isinstance(dv,dict): fail("feature gate domain_verification not declared")
 missing_verification=sorted(d for d in declared_domains if not isinstance(dv.get(d),list) or not dv[d])
 if missing_verification: fail("feature gate domains lack verification: "+",".join(missing_verification))
 allowed_refs=set(f["source_paths"]+f["audits"]+f["tests"])
 policy=json.loads((ROOT/"v2/gates/domain_verification_policy.json").read_text(encoding="utf-8"))
 kind_paths={"source":set(f["source_paths"]),"audit":set(f["audits"]),"test":set(f["tests"]),"device":set(f["device_checks"])}
 for domain,refs in dv.items():
  if domain not in declared_domains: fail("feature gate verification references undeclared domain: "+domain)
  unknown_refs=sorted(set(refs)-allowed_refs)
  if unknown_refs: fail("feature gate domain verification uses undeclared paths: "+domain+" -> "+",".join(unknown_refs))
  required_kinds=policy.get("rules",{}).get(domain,policy.get("default_required_kinds",["source"]))
  for kind in required_kinds:
   if not any(ref in kind_paths.get(kind,set()) for ref in refs): fail("feature gate domain lacks required verification kind: "+domain+" -> "+kind)
 traces=json.loads((ROOT/"v2/gates/traceability.json").read_text(encoding="utf-8")).get("traces",[])
 trace_by_id={t["decision_id"]:t for t in traces}
 for rid in f["requirements"]:
  t=trace_by_id.get(rid)
  if not t or t.get("state")!="consumed": fail("feature requirement not consumed by rebuilt design: "+rid)
  if not t.get("design_ref") or not t.get("verification"): fail("feature requirement lacks design/verification trace: "+rid)
 for key in ("source_paths","audits","tests"):
  for rel in f[key]:
   if not (ROOT/rel).exists(): fail("feature gate "+key+" path missing: "+rel)
print("CB6 DEVELOPMENT GATE PASS: implementation enabled")
