#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
v14=json.loads((R/"v2/gates/operational_rule_registry_v14.json").read_text());v15=json.loads((R/"v2/gates/operational_rule_registry_v15.json").read_text())
cov=json.loads((R/"v2/gates/rule_coverage.json").read_text());ad=json.loads((R/"v2/gates/development_efficiency_adoption_evidence_v2.json").read_text());c=json.loads((R/"v2/gates/development_efficiency_rule_candidate_v2.json").read_text())
if v15.get("version")!=15 or v15.get("status")!="ACTIVE" or v15.get("supersedes")!="v2/gates/operational_rule_registry_v14.json":e.append("v15 identity")
a14={x["id"]:x for x in v14["rules"]};a15={x["id"]:x for x in v15["rules"]}
for k,v in a14.items():
 if k!="OPS-DEVELOPMENT-EFFICIENCY-001" and a15.get(k)!=v:e.append("unrelated ACTIVE rule changed:"+k)
x=a15.get("OPS-DEVELOPMENT-EFFICIENCY-001",{})
if x.get("status")!="ACTIVE" or x.get("contract")!="v2/gates/development_efficiency_rule_candidate_v2.json":e.append("v2 registry binding")
if cov.get("registry")!="v2/gates/operational_rule_registry_v15.json" or not any(z.get("rule_id")=="OPS-DEVELOPMENT-EFFICIENCY-001" and z.get("coverage_status")=="MACHINE_ENFORCED" for z in cov.get("entries",[])):e.append("coverage")
if c.get("status")!="ACTIVE" or c.get("revision")!=2:e.append("contract not ACTIVE v2")
if ad.get("status")!="ACTIVE" or ad.get("authority",{}).get("decision")!="Development Efficiency v2を正式採用してACTIVE化を承認して進めて":e.append("adoption")
for k,v in c.get("requirements",{}).items():
 if v is not True:e.append("requirement weakened:"+k)
if e:
 print("CB6 DEVELOPMENT EFFICIENCY ACTIVE V2 FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT EFFICIENCY ACTIVE V2 PASS")
