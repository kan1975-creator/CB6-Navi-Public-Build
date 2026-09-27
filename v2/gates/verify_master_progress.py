#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ledger=json.loads((ROOT/"v2/gates/cb6_master_progress.json").read_text())
dec=json.loads((ROOT/"v2/gates/active_decisions.json").read_text())
active={x["id"] for x in dec["decisions"] if x.get("status")=="active"}
listed={x["id"] for x in ledger.get("specifications",[])}
if active!=listed:
 print("CB6 MASTER LEDGER FAIL: active specification coverage mismatch",sorted(active-listed),sorted(listed-active)); raise SystemExit(1)
required={"ROOT","METHOD","FEATURES","APK","DEVICE","FINAL"}
stages={x["id"] for x in ledger.get("progress_pipeline",[])}
if stages!=required:
 print("CB6 MASTER LEDGER FAIL: progress pipeline incomplete"); raise SystemExit(1)
for x in ledger["specifications"]:
 if not x.get("spec_key") or not x.get("requirement") or not x.get("evidence"):
  print("CB6 MASTER LEDGER FAIL: specification basis incomplete",x.get("id")); raise SystemExit(1)
for p in ledger.get("reconstruction",[]):
 if not (ROOT/p).exists():
  print("CB6 MASTER LEDGER FAIL: reconstruction path missing",p); raise SystemExit(1)
print("CB6 MASTER DEVELOPMENT LEDGER PASS:",len(active),"active specifications covered")

# Preserve partial/deferred history and prevent accidental restart semantics.
overrides=ledger.get("progress_overrides",{})
for req_id,state in overrides.items():
    if req_id not in active:
        print("CB6 MASTER LEDGER FAIL: progress override is not active",req_id); raise SystemExit(1)
    if state.get("restart_from_zero") is not False:
        print("CB6 MASTER LEDGER FAIL: restart semantics not explicit",req_id); raise SystemExit(1)
    if not state.get("achieved") or not state.get("unresolved") or not state.get("resume_from"):
        print("CB6 MASTER LEDGER FAIL: partial/deferred history incomplete",req_id); raise SystemExit(1)
    if state.get("implementation_state")=="DEFERRED_WITH_EVIDENCE" and not state.get("deferred_reason"):
        print("CB6 MASTER LEDGER FAIL: deferred reason missing",req_id); raise SystemExit(1)
print("CB6 MASTER RESUME STATE PASS:",len(overrides),"tracked partial/deferred requirements")

# Master source-inventory closure: no required authority/evidence source may silently disappear.
inventory=ledger.get("source_inventory",[])
for item in inventory:
    p=item.get("path","")
    if not p:
        print("CB6 MASTER LEDGER FAIL: empty source inventory path"); raise SystemExit(1)
    if p.endswith(("features","research_records","impact_records")):
        if not (ROOT/p).is_dir():
            print("CB6 MASTER LEDGER FAIL: source directory missing",p); raise SystemExit(1)
    elif not (ROOT/p).exists():
        print("CB6 MASTER LEDGER FAIL: source inventory file missing",p); raise SystemExit(1)
required_failure_ids={"STALE_VALIDATOR","ESCAPED_NEWLINE","LATER_PATCH_RESTORE","USERMARK_GROUP_MISMATCH","GROUP_REPLACEMENT","BUILD_NOT_FEATURE_SUCCESS","MWM_DUPLICATED_BY_NETWORK","CONTEXT_CONTINUITY","REPEATED_STALE_AUDIT"}
actual_failure_ids={x.get("id") for x in ledger.get("known_failure_classes",[])}
if required_failure_ids-actual_failure_ids:
    print("CB6 MASTER LEDGER FAIL: known failure coverage missing",sorted(required_failure_ids-actual_failure_ids)); raise SystemExit(1)
if not ledger.get("completeness",{}).get("zero_omission_required"):
    print("CB6 MASTER LEDGER FAIL: zero-omission rule missing"); raise SystemExit(1)
print("CB6 MASTER SOURCE/HISTORY COVERAGE PASS")

# Explicit development-order coverage: prohibit ambiguous catch-all buckets.
order_rows=ledger.get("development_order",[])
if len(order_rows)!=22 or [x.get("order") for x in order_rows] != list(range(22)):
    print("CB6 MASTER LEDGER FAIL: development order must be explicit contiguous 0..21"); raise SystemExit(1)
if any(x.get("id") in {"OTHER_POI_AND_CONTROLS","OTHER_FEATURES","MISC"} for x in order_rows):
    print("CB6 MASTER LEDGER FAIL: catch-all development bucket forbidden"); raise SystemExit(1)
mapped=set()
for row in order_rows:
    mapped.update(row.get("requirements",[]))
# PROC requirements govern the pipeline rather than one feature row.
required_order_ids={x["id"] for x in ledger.get("specifications",[]) if not x["id"].startswith("PROC-")}
missing_order=required_order_ids-mapped
if missing_order:
    print("CB6 MASTER LEDGER FAIL: active product requirements missing from development order",sorted(missing_order)); raise SystemExit(1)
print("CB6 MASTER DEVELOPMENT ORDER PASS:",len(order_rows),"explicit stages")
