#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
SCHEMA=R/"v2/gates/development_auditor_work_unit_schema_v1.json"
MANDATORY={"freshness","active_authority","user_intent","applicable_rules_and_method","approval_boundary","change_impact","known_failures","actual_scope","unresolved_blockers"}
STATES=["RECONSTRUCT","CLASSIFY","RESEARCH","AUDIT","PROPOSE","APPROVAL_BOUND","IMPLEMENTED","VALIDATED","INDEPENDENTLY_REVIEWED","EXIT_AUDITED","PASS"]
def check(d,current_head=None):
 e=[]; s=json.loads(SCHEMA.read_text())
 for k in s["required"]:
  if k not in d:e.append("missing work-unit field: "+k)
 if e:return e
 if d.get("state_history")!=STATES[:len(d.get("state_history",[]))]:e.append("invalid state transition order")
 if d.get("outcome")=="PASS" and d.get("state_history")!=STATES:e.append("PASS before complete state chain")
 dims={x.get("name"):x for x in d.get("dimensions",[]) if isinstance(x,dict)}
 for n in MANDATORY:
  if n not in dims:e.append("missing mandatory dimension: "+n);continue
  x=dims[n]
  for k in s["dimension_required"]:
   if k not in x:e.append(f"{n}: missing {k}")
  if x.get("applicability")=="BLOCKED" and d.get("outcome")=="PASS":e.append(n+": blocked dimension cannot PASS")
  if x.get("unresolved_items") and d.get("outcome")=="PASS":e.append(n+": unresolved items cannot PASS")
  if not x.get("evidence_refs"):e.append(n+": concrete evidence missing")
 a=d.get("approval",{})
 for k in ("approval_id","approved_at","proposed_change_id","approved_change_summary","github_reference"):
  if not a.get(k):e.append("approval missing: "+k)
 if a.get("proposed_change_id")!=d.get("change_id"):e.append("approval change binding mismatch")
 if a.get("basis_head")!=d.get("basis_head"):e.append("approval basis HEAD mismatch")
 if set(a.get("planned_paths",[]))!=set(d.get("planned_paths",[])):e.append("approval planned paths mismatch")
 if set(a.get("affected_domains",[]))!=set(d.get("affected_domains",[])):e.append("approval affected domains mismatch")
 if set(a.get("forbidden_scope",[]))!=set(d.get("forbidden_scope",[])):e.append("approval forbidden scope mismatch")
 if a.get("approved_at","")>=d.get("implementation_started_at",""):e.append("approval is not pre-implementation")
 if current_head and d.get("target_head")!=current_head:e.append("stale target HEAD")
 diff=set(d.get("actual_diff",{}).get("paths",[])); planned=set(d.get("planned_paths",[]))
 if not diff.issubset(planned):e.append("actual diff outside approved planned paths")
 forbidden=set(d.get("forbidden_scope",[]))
 if diff & forbidden:e.append("actual diff intersects forbidden scope")
 v=d.get("validation",{})
 if d.get("outcome")=="PASS" and (v.get("complete") is not True or not v.get("evidence_refs")):e.append("validation incomplete")
 ir=d.get("independent_review",{})
 if d.get("outcome")=="PASS" and (ir.get("accepted") is not True or ir.get("blocking_disagreement") is True or not ir.get("evidence_refs")):e.append("independent review incomplete or blocking")
 if d.get("outcome")=="PASS" and d.get("exit_audit",{}).get("accepted") is not True:e.append("exit audit not accepted")
 return e
if __name__=="__main__":
 if len(sys.argv)<2:raise SystemExit("usage: verify_development_auditor_work_unit_v2.py work-unit.json [current-head]")
 d=json.loads(Path(sys.argv[1]).read_text()); e=check(d,sys.argv[2] if len(sys.argv)>2 else None)
 if e:
  print("CB6 DEVELOPMENT AUDITOR WORK UNIT FAIL:",*e,sep="\n - ");raise SystemExit(1)
 print("CB6 DEVELOPMENT AUDITOR WORK UNIT PASS: real work-unit state, approval, HEAD, diff, validation, independent review and exit audit are bound")
