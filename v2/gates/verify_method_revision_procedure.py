#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; d=json.loads((R/"v2/gates/method_revision_procedure_v1.json").read_text()); e=[]
if d.get("status") not in ("CANDIDATE","INDEPENDENTLY_REVIEWED","ACTIVE_REFROZEN"): e.append("procedure status invalid")
if d.get("status")!="CANDIDATE" and d.get("adoption_evidence")!="v2/gates/governance_adoption_evidence.json": e.append("procedure adoption evidence missing")
if d.get("status")=="ACTIVE_REFROZEN":
 p=R/"v2/gates/governance_postchange_certification.json"
 if d.get("postchange_evidence")!="v2/gates/governance_postchange_certification.json" or not p.is_file(): e.append("ACTIVE_REFROZEN postchange evidence missing")
 else:
  x=json.loads(p.read_text()); dg=x.get("development_gate",{}); rf=x.get("root_certification",{}); mf=x.get("method_freeze",{})
  if x.get("status")!="CERTIFIED" or dg.get("run_id")!=36664054828 or dg.get("conclusion")!="success" or dg.get("head_sha")!="b3064ba3855eed1ef511424b5dd9f4796d03a3f4" or rf.get("status")!="PROVEN" or mf.get("result")!="PASS": e.append("ACTIVE_REFROZEN postchange evidence invalid")
if not d.get("basis_head"): e.append("basis head missing")
a=d.get("authority_split",{})
if a.get("revision_intent")!="explicit_user_decision" or a.get("verification")!="github_executable_evidence" or a.get("final_adoption")!="explicit_user_adoption_after_evidence": e.append("authority split invalid")
expected=["PROPOSED","IMPLEMENTED_UNVERIFIED","MACHINE_VERIFIED","INDEPENDENTLY_REVIEWED","ACTIVE_REFROZEN"]
if d.get("states")!=expected: e.append("revision states invalid")
inv=d.get("invariants",{})
for k in ("direct_freeze_hash_rewrite_forbidden","candidate_cannot_verify_its_own_adoption","prechange_authority_must_remain_available_until_adoption","failed_or_missing_evidence_blocks_activation","reasonless_revision_forbidden","silent_contradiction_with_prior_decision_forbidden"):
 if inv.get(k) is not True: e.append("invariant weakened: "+k)
seq=d.get("required_sequence",[])
required={"record_reason_and_affected_frozen_files","record_prechange_head_and_freeze_lock","implement_candidate_without_overwriting_current_active_authority","run_candidate_positive_and_destructive_verification","record_successful_github_run_evidence","perform_independent_review_against_prechange_authority_and_candidate","obtain_explicit_user_adoption","update_active_method_authority","regenerate_freeze_lock_from_adopted_files","run_full_root_certification_and_development_gate","record_postchange_head_and_run_evidence"}
if set(seq)!=required or len(seq)!=len(required): e.append("revision sequence incomplete or duplicated")
if e:
 print("CB6 METHOD REVISION PROCEDURE FAIL:")
 for x in e: print(" -",x)
 raise SystemExit(1)
print(f"CB6 METHOD REVISION PROCEDURE PASS: status={d.get('status')}; direct_hash_rewrite=forbidden; self_adoption=forbidden; sequence=complete")
