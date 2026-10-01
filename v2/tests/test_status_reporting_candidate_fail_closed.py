#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];base=json.loads((R/"v2/gates/status_reporting_contract_candidate_v1.json").read_text(encoding="utf-8"));cases=[]
def add(n,fn):d=json.loads(json.dumps(base));fn(d);cases.append((n,d))
add("tag_not_required_at_start",lambda d:d["report_tags"].__setitem__("required_at_report_start",False))
add("governance_tag_not_required",lambda d:d["report_tags"].__setitem__("governance_report_requires","その他"))
add("tag_replaces_classification",lambda d:d["report_tags"].__setitem__("tag_presence_does_not_replace_status_classification",False))
add("unknown_tag_removed",lambda d:d["report_tags"].__setitem__("allowed",["Governance","Signal","Convenience"]))
add("fourth_class",lambda d:d["allowed_classifications"].append("その他"))
add("not_exactly_one",lambda d:d.__setitem__("exactly_one_classification_required",False))
add("not_all_33",lambda d:d["scope"].__setitem__("all_33_items_mandatory",False))
add("count_not_33",lambda d:d["scope"].__setitem__("consolidated_worklist_required_item_count",32))
add("derivative_scope_removed",lambda d:d["scope"].__setitem__("applies_to_all_derivative_work",False))
add("future_scope_removed",lambda d:d["scope"].__setitem__("applies_to_all_future_work",False))
add("unknown_future_removed",lambda d:d["scope"].__setitem__("applies_to_unknown_future_features_without_enumeration",False))
add("feature_override_allowed",lambda d:d["scope"].__setitem__("feature_specific_override_may_weaken_or_disable",True))
add("future_opt_in_required",lambda d:d["scope"].__setitem__("new_feature_requires_explicit_opt_in",True))
add("fresh_head_disabled",lambda d:d["freshness_rule"].__setitem__("progress_query_requires_current_head",False))
add("investigation_is_fix_permission",lambda d:d["fix_approval_boundary"].__setitem__("investigation_permission_is_not_fix_permission",False))
add("generic_progress_is_fix_approval",lambda d:d["fix_approval_boundary"].__setitem__("generic_progress_permission_is_not_specific_fix_approval",False))
add("old_approval_reuse",lambda d:d["fix_approval_boundary"].__setitem__("old_approval_reuse_for_different_change_forbidden",False))
add("direct_activation",lambda d:d["activation"].__setitem__("direct_active_forbidden",False))
for name,d in cases:
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);shutil.copytree(R/"v2",t/"v2");(t/"v2/gates/status_reporting_contract_candidate_v1.json").write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  p=subprocess.run(["python3",str(t/"v2/gates/verify_status_reporting_candidate.py")],cwd=t,capture_output=True,text=True)
  if p.returncode==0:raise SystemExit("destructive case unexpectedly passed: "+name)
print("CB6 STATUS REPORTING DESTRUCTIVE PASS:",len(cases),"weakenings rejected")
