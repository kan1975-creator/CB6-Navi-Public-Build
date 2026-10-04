#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
v10=json.loads((R/"v2/gates/operational_rule_registry_v10.json").read_text());v11=json.loads((R/"v2/gates/operational_rule_registry_v11.json").read_text());v12=json.loads((R/"v2/gates/operational_rule_registry_v12.json").read_text());cov=json.loads((R/"v2/gates/rule_coverage.json").read_text());ad=json.loads((R/"v2/gates/development_efficiency_adoption_evidence.json").read_text());cand=json.loads((R/"v2/gates/development_efficiency_rule_candidate.json").read_text())
if v11.get("version")!=11 or v11.get("status")!="ACTIVE" or v11.get("supersedes")!="v2/gates/operational_rule_registry_v10.json":e.append("v11 identity")
if v12.get("version")!=12 or v12.get("status")!="ACTIVE" or v12.get("supersedes")!="v2/gates/operational_rule_registry_v11.json":e.append("v12 identity")
a10={x["id"]:x for x in v10["rules"]};a11={x["id"]:x for x in v11["rules"]};a12={x["id"]:x for x in v12["rules"]}
for k,v in a10.items():
 if a11.get(k)!=v:e.append("v10 ACTIVE rule changed:"+k)
for k,v in a11.items():
 if k!="OPS-STATUS-REPORTING-001" and a12.get(k)!=v:e.append("v11 ACTIVE rule changed:"+k)
x=a12.get("OPS-DEVELOPMENT-EFFICIENCY-001",{})
if x.get("status")!="ACTIVE" or x.get("scope")!="all_current_features_all_future_features_all_33_items_and_derivative_work":e.append("efficiency rule not ACTIVE cross-cutting")
if cov.get("registry")!="v2/gates/operational_rule_registry_v12.json" or not any(z.get("rule_id")=="OPS-DEVELOPMENT-EFFICIENCY-001" and z.get("coverage_status")=="MACHINE_ENFORCED" for z in cov.get("entries",[])):e.append("coverage")
if ad.get("authority",{}).get("decision")!="OPS-DEVELOPMENT-EFFICIENCY-001を採用して進めて" or ad.get("evidence",{}).get("candidate_gate",{}).get("run_id")!=37135315388 or ad.get("evidence",{}).get("independent_review",{}).get("run_id")!=37135558644:e.append("adoption evidence")
for k,v in cand.get("requirements",{}).items():
 if v is not True:e.append("candidate requirement weakened:"+k)
if e:
 print("CB6 DEVELOPMENT EFFICIENCY ACTIVE FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("CB6 DEVELOPMENT EFFICIENCY ACTIVE PASS: v10/v11 preserved; v12 active; coverage machine-enforced")
