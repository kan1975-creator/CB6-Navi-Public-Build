#!/usr/bin/env python3
"""Evidence Inventory integrity gate."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def stop(message): raise SystemExit("CB6 EVIDENCE FAIL: "+message)
state=json.loads((ROOT/"v2/gates/project_state.json").read_text(encoding="utf-8"))
inventory=json.loads((ROOT/"v2/gates/evidence_inventory.json").read_text(encoding="utf-8"))
registry=json.loads((ROOT/"v2/gates/active_decisions.json").read_text(encoding="utf-8"))
if inventory.get("schema") != 1: stop("unsupported schema")
if inventory.get("stage") != state.get("stage"): stop("stage mismatch")
rows=inventory.get("evidence",[])
if not rows: stop("empty inventory")
allowed={"active","historical-mixed","historical","retired","revalidation-required"}
ids=[]; paths=[]
for row in rows:
    if not all(row.get(k) for k in ("id","type","path","status")): stop("incomplete row")
    ids.append(row["id"]); paths.append(row["path"])
    if row["status"] not in allowed: stop("invalid status "+row["id"])
    if not (ROOT/row["path"]).is_file(): stop("missing evidence path "+row["path"])
if len(ids)!=len(set(ids)): stop("duplicate evidence id")
if len(paths)!=len(set(paths)): stop("duplicate evidence path")
stale={row["path"] for row in rows if row["status"]=="revalidation-required"}
for decision in registry.get("decisions",[]):
    if decision.get("status")=="active" and stale.intersection(decision.get("evidence",[])):
        stop("active requirement depends on stale evidence "+decision.get("id","?"))
print("CB6 EVIDENCE PASS:",len(rows),"classified records; stale evidence is isolated from active requirements")
