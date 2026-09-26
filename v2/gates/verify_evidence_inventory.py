#!/usr/bin/env python3
"""Fail-closed validation for the CB6 Evidence Inventory."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(msg): raise SystemExit("CB6 EVIDENCE FAIL: "+msg)
def load(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8"))
state=load("v2/gates/project_state.json")
inv=load("v2/gates/evidence_inventory.json")
reg=load("v2/gates/active_decisions.json")
if inv.get("schema")!=1: fail("unsupported inventory schema")
if inv.get("stage")!=state.get("stage"): fail("inventory stage mismatch")
rows=inv.get("evidence")
if not isinstance(rows,list) or not rows: fail("inventory empty")
allowed={"active","historical-mixed","historical","retired","revalidation-required"}
ids=set(); paths=set()
for row in rows:
    for key in ("id","type","path","status"):
        if not row.get(key): fail("inventory row missing "+key)
    if row["id"] in ids: fail("duplicate evidence id: "+row["id"])
    if row["path"] in paths: fail("duplicate evidence path: "+row["path"])
    if row["status"] not in allowed: fail("invalid evidence status: "+row["id"])
    if not (ROOT/row["path"]).is_file(): fail("inventory path missing: "+row["path"])
    ids.add(row["id"]); paths.add(row["path"])
# Every repository-file evidence cited by a requirement must be classified.
for d in reg.get("decisions",[]):
    for ev in d.get("evidence",[]):
        if isinstance(ev,str) and ev.startswith(("docs/","v2/","AGENTS.md","CLAUDE_HANDOVER.md")):
            if ev not in paths: fail(f"{d.get('id')} cites unclassified evidence: {ev}")
# Revalidation-required evidence is stale by definition and cannot support an active requirement.
stale={r["path"] for r in rows if r["status"]=="revalidation-required"}
for d in reg.get("decisions",[]):
    if d.get("status")=="active":
        hit=stale.intersection(d.get("evidence",[]))
        if hit: fail(f"{d.get('id')} depends on revalidation-required evidence: {sorted(hit)[0]}")
print(f"CB6 EVIDENCE PASS: {len(rows)} classified evidence records; active requirements contain no stale dependency")
