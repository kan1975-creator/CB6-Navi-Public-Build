#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
reg=json.loads((R/"v2/gates/operational_rule_registry_v4.json").read_text())
if reg.get("version")!=4 or reg.get("status")!="ACTIVE":e.append("v4 registry not ACTIVE")
f=reg.get("cross_cutting_foundation",{})
if f.get("id")!="CB6-CROSS-CUTTING-RULE-FOUNDATION-001" or f.get("status")!="ACTIVE":e.append("foundation not ACTIVE")
if f.get("inheritance")!="ALL_ACTIVE_CROSS_CUTTING_RULES":e.append("inheritance weakened")
if f.get("scope")!="all_current_features_all_future_features_all_33_items_and_derivative_work":e.append("scope weakened")
r3=json.loads((R/"v2/gates/operational_rule_registry_v3.json").read_text())
a3={x["id"] for x in r3.get("rules",[]) if x.get("status")=="ACTIVE"};a4={x["id"] for x in reg.get("rules",[]) if x.get("status")=="ACTIVE"}
if a3!=a4 or len(a4)!=11:e.append("v3 ACTIVE rules not preserved exactly")
for p in sorted((R/"v2/gates/features").glob("*.json")):
 d=json.loads(p.read_text())
 if d.get("inherits_cross_cutting_rules")!="ALL_ACTIVE_CROSS_CUTTING_RULES":e.append("feature inheritance missing: "+str(p.relative_to(R)))
ad=json.loads((R/"v2/gates/cross_cutting_rule_foundation_adoption_evidence.json").read_text())
if ad.get("authority",{}).get("decision")!="CB6-CROSS-CUTTING-RULE-FOUNDATION-001を採用して進めて":e.append("explicit adoption evidence missing")
if e:
 print("CB6 CROSS-CUTTING FOUNDATION ACTIVE FAIL:")
 for x in e:print(" -",x)
 raise SystemExit(1)
print("CB6 CROSS-CUTTING FOUNDATION ACTIVE PASS: v3_active_rules=11 preserved; current+future feature inheritance enforced")
