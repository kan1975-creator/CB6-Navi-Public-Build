#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];e=[]
reg=json.loads((R/"v2/gates/operational_rule_registry_v15.json").read_text());cov=json.loads((R/"v2/gates/rule_coverage.json").read_text());c=json.loads((R/"v2/gates/apk_build_preflight_candidate.json").read_text());a=json.loads((R/"v2/gates/apk_build_preflight_adoption_evidence.json").read_text())
rules={x["id"]:x for x in reg["rules"]};x=rules.get("OPS-APK-BUILD-PREFLIGHT-001",{})
if reg.get("version")!=15 or reg.get("supersedes")!="v2/gates/operational_rule_registry_v14.json":e.append("registry identity")
if x.get("status")!="ACTIVE" or x.get("contract")!="v2/gates/apk_build_preflight_candidate.json":e.append("active registry binding")
if c.get("status")!="ACTIVE" or c.get("fail_closed") is not True or c.get("placement")!="immediately_before_gradle_apk_build":e.append("active contract")
if not all(v is True for v in c.get("requirements",{}).values()):e.append("requirements weakened")
if cov.get("registry")!="v2/gates/operational_rule_registry_v20.json" or not any(z.get("rule_id")=="OPS-APK-BUILD-PREFLIGHT-001" and z.get("coverage_status")=="MACHINE_ENFORCED" for z in cov.get("entries",[])):e.append("coverage")
if a.get("status")!="ACTIVE" or a.get("authority",{}).get("decision")!="OPS-APK-BUILD-PREFLIGHT-001を正式採用してACTIVE化を承認して進めて" or a.get("next_required")!=[]:e.append("adoption")
if a.get("evidence",{}).get("candidate_gate",{}).get("run_id")!=37277837844 or a.get("evidence",{}).get("independent_review",{}).get("run_id")!=37283457168:e.append("evidence")
if e: print("APK BUILD PREFLIGHT ACTIVE FAIL:",*e,sep="\n - ");raise SystemExit(1)
print("APK BUILD PREFLIGHT ACTIVE PASS")
