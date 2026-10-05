#!/usr/bin/env python3
import copy,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2]
reg=json.loads((R/"v2/gates/operational_rule_registry_v15.json").read_text());cov=json.loads((R/"v2/gates/rule_coverage.json").read_text());c=json.loads((R/"v2/gates/apk_build_preflight_candidate.json").read_text());a=json.loads((R/"v2/gates/apk_build_preflight_adoption_evidence.json").read_text())
def ok(r,v,d,e):
 x={z["id"]:z for z in r["rules"]}.get("OPS-APK-BUILD-PREFLIGHT-001",{})
 return r.get("version")==15 and x.get("status")=="ACTIVE" and d.get("status")=="ACTIVE" and d.get("fail_closed") is True and all(d.get("requirements",{}).values()) and v.get("registry")=="v2/gates/operational_rule_registry_v17.json" and any(z.get("rule_id")=="OPS-APK-BUILD-PREFLIGHT-001" and z.get("coverage_status")=="MACHINE_ENFORCED" for z in v["entries"]) and e.get("status")=="ACTIVE"
assert ok(reg,cov,c,a)
x=copy.deepcopy(c);x["fail_closed"]=False;assert not ok(reg,cov,x,a)
x=copy.deepcopy(c);x["requirements"]["generated_source_integration_checked"]=False;assert not ok(reg,cov,x,a)
x=copy.deepcopy(reg);[z.update({"status":"PROPOSED"}) for z in x["rules"] if z["id"]=="OPS-APK-BUILD-PREFLIGHT-001"];assert not ok(x,cov,c,a)
x=copy.deepcopy(cov);[z.update({"coverage_status":"DOCUMENTED_ONLY"}) for z in x["entries"] if z["rule_id"]=="OPS-APK-BUILD-PREFLIGHT-001"];assert not ok(reg,x,c,a)
print("APK BUILD PREFLIGHT ACTIVE DESTRUCTIVE PASS")
