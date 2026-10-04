#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_active_v8.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v8 independent review baseline failed")
cases=[
 ("allow-fixed",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"].update({"fixed_or_unsubstantiated_estimate_forbidden":False}),"all-process wait evidence guard invalid"),
 ("drop-start",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["required_evidence"].remove("current_run_or_step_start_time"),"required wait evidence missing"),
 ("drop-elapsed",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["required_evidence"].remove("current_elapsed_time"),"required wait evidence missing"),
 ("drop-history",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["required_evidence"].remove("same_or_reasonably_comparable_historical_actual_duration_when_available"),"required wait evidence missing"),
 ("invent-unknown",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"].update({"no_comparable_history_behavior":"FIXED_5_MINUTES"}),"unknown-duration fallback invalid"),
 ("drop-future",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["applies_to"].remove("all_future_CB6_waiting_processes"),"future wait-process coverage missing"),
 ("unlabeled-reference",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"must_be_labeled_as_reference_estimate":False}),"reference estimate guard invalid"),
 ("reference-replaces-unknown",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"official_next_check_guidance_remains":"5分"}),"reference estimate replaced official unknown-duration guidance"),
 ("unsupported-reference",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"unsupported_guess_forbidden":False}),"reference estimate guard invalid"),
 ("reference-always-visible",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"display_condition":"ALWAYS"}),"reference estimate display condition invalid"),
 ("reference-with-official",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"forbidden_when_official_guidance_is_evidence_based":False}),"reference estimate conditional display guard invalid"),
 ("omit-supported-reference",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"display_required_when_duration_unknown_and_supported_basis_available":False}),"reference estimate conditional display guard invalid"),
 ("always-show-basis",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"basis_detail_normally_hidden":False}),"reference estimate conditional display guard invalid"),
 ("hide-basis-on-request",lambda d:d["rules"]["待ち"]["wait_time_display"]["evidence_based_estimate"]["reference_estimate_when_no_comparable_actual_history"].update({"show_basis_detail_when_user_asks":False}),"reference estimate conditional display guard invalid"),
 ("change-v7",lambda d:d["final_summary_display"].update({"duplicate_information_forbidden":False}),"existing ACTIVE v7 contract changed"),
 ("self-active",lambda d:d.update({"status":"CANDIDATE"}),"active v8 identity/status invalid")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_v8.json"; q=json.loads(p.read_text()); mut(q); p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v8-review rejection:",name)
print("PASS status reporting v8 all-process wait-evidence destructive cases rejected")
