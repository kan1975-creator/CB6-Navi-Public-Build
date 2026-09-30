#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];base=json.loads((R/"v2/gates/cross_cutting_rule_foundation_candidate.json").read_text());cases=[]
def add(n,fn):d=json.loads(json.dumps(base));fn(d);cases.append((n,d))
add("future_off",lambda d:d["scope"].__setitem__("all_future_features",False))
add("all33_off",lambda d:d["scope"].__setitem__("all_33_consolidated_items",False))
add("opt_in",lambda d:d["scope"].__setitem__("feature_opt_in_required",True))
add("override",lambda d:d["scope"].__setitem__("feature_override_may_weaken",True))
add("inheritance_off",lambda d:d["feature_contract_inheritance"].__setitem__("automatic",False))
add("per_rule_wiring",lambda d:d["feature_contract_inheritance"].__setitem__("new_feature_must_inherit_without_per_rule_wiring",False))
add("investigation_equals_fix",lambda d:d["approval_semantics"].__setitem__("investigation_and_read_only_distinct_from_fix_approval",False))
add("binding_off",lambda d:d["approval_semantics"].__setitem__("exact_change_binding_required",False))
add("reuse",lambda d:d["approval_semantics"].__setitem__("reuse_for_different_change_forbidden",False))
add("posthoc",lambda d:d["approval_semantics"].__setitem__("post_hoc_forbidden",False))
add("missing_ok",lambda d:d["approval_semantics"].__setitem__("missing_approval_forbidden",False))
add("direct_active",lambda d:d["lifecycle"].__setitem__("direct_active_forbidden",False))
for name,d in cases:
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);shutil.copytree(R/"v2",t/"v2");(t/"v2/gates/cross_cutting_rule_foundation_candidate.json").write_text(json.dumps(d,ensure_ascii=False,indent=2))
  p=subprocess.run(["python3",str(t/"v2/gates/verify_cross_cutting_rule_foundation_candidate.py")],cwd=t,capture_output=True,text=True)
  if p.returncode==0:raise SystemExit("destructive case unexpectedly passed: "+name)
print("CB6 CROSS-CUTTING FOUNDATION DESTRUCTIVE PASS:",len(cases),"weakenings rejected")
