#!/usr/bin/env python3
import importlib.util,pathlib,copy
P=pathlib.Path(__file__).resolve().parents[1]/"gates"/"verify_development_auditor_work_unit_v2.py"
s=importlib.util.spec_from_file_location("v",P);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
dims=[{"name":n,"applicability":"APPLIED","evidence_refs":["repo:evidence"],"finding":"ok","counter_hypothesis_or_alternative":"checked","unresolved_items":[],"impact_scope":["governance"]} for n in v.MANDATORY]
base={"change_id":"AUDITOR-V2-RUNTIME-001","basis_head":"5001dd55aebd7a510765ac8f9a9843bcaa77d6d6","target_head":"TARGET","purpose":"runtime enforcement","change_type":"governance","affected_domains":["auditor"],"planned_paths":["v2/gates/x"],"forbidden_scope":["v2/signals/x"],"authority":["CB6-DEVELOPMENT-AUDITOR-V2"],"dimensions":dims,"approval":{"approval_id":"USER-20261006-AUDITOR-V2-RUNTIME","approved_at":"2026-10-06T08:30:00Z","proposed_change_id":"AUDITOR-V2-RUNTIME-001","approved_change_summary":"runtime enforcement","github_reference":"chat-explicit-approval-2026-10-06","basis_head":"5001dd55aebd7a510765ac8f9a9843bcaa77d6d6","planned_paths":["v2/gates/x"],"affected_domains":["auditor"],"forbidden_scope":["v2/signals/x"]},"implementation_started_at":"2026-10-06T08:31:00Z","actual_diff":{"paths":["v2/gates/x"]},"validation":{"complete":True,"evidence_refs":["run:test"]},"independent_review":{"accepted":True,"blocking_disagreement":False,"evidence_refs":["run:ir"]},"exit_audit":{"accepted":True},"outcome":"PASS","state_history":v.STATES}
assert not v.check(base,"TARGET")
cases=[]
def bad(label,mut,needle):
 x=copy.deepcopy(base);mut(x);cases.append((label,x,needle))
bad("missing-work-unit",lambda x:x.pop("change_id"),"missing work-unit field")
bad("approval-missing",lambda x:x["approval"].pop("approval_id"),"approval missing")
bad("stale-head",lambda x:x.update(target_head="OLD"),"stale target HEAD")
bad("scope-drift",lambda x:x["actual_diff"]["paths"].append("outside/path"),"actual diff outside")
bad("validation",lambda x:x["validation"].update(complete=False),"validation incomplete")
bad("ir-missing",lambda x:x["independent_review"].update(accepted=False),"independent review incomplete")
bad("ir-blocking",lambda x:x["independent_review"].update(blocking_disagreement=True),"independent review incomplete")
bad("exit",lambda x:x["exit_audit"].update(accepted=False),"exit audit not accepted")
bad("state-order",lambda x:x.update(state_history=["RECONSTRUCT","AUDIT"]),"invalid state transition")
for label,x,needle in cases:
 e=v.check(x,"TARGET")
 if not any(needle in z for z in e):raise SystemExit(label+" not rejected: "+repr(e))
 print("PASS expected work-unit rejection:",label)
print("CB6 DEVELOPMENT AUDITOR WORK UNIT DESTRUCTIVE PASS")
