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
