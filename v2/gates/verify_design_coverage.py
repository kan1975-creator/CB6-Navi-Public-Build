#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(m): raise SystemExit("CB6 DESIGN COVERAGE FAIL: "+m)
coverage=json.loads((ROOT/"v2/gates/design_coverage.json").read_text())
decisions=json.loads((ROOT/"v2/gates/active_decisions.json").read_text())
state=json.loads((ROOT/"v2/gates/project_state.json").read_text())
if set(coverage)!={"schema","stage","canonical_design_target","required_sections"} or coverage["schema"]!=1 or coverage["stage"]!=state["stage"]: fail("coverage contract invalid")
active={x["id"] for x in decisions["decisions"] if x.get("status")=="active"}
covered=[]
for s in coverage["required_sections"]:
 if set(s)!={"section","requirements"} or not s["section"] or not s["requirements"]: fail("coverage section invalid")
 covered.extend(s["requirements"])
if len(covered)!=len(set(covered)): fail("requirement covered more than once")
if set(covered)!=active: fail("active decision coverage mismatch")
target=ROOT/coverage["canonical_design_target"]
if target.exists():
 text=target.read_text(encoding="utf-8")
 for s in coverage["required_sections"]:
  if f"## {s['section']}" not in text: fail("design section missing: "+s["section"])
  for rid in s["requirements"]:
   if rid not in text: fail("design omits active decision: "+rid)
print("CB6 DESIGN COVERAGE PASS:",len(active),"active decisions mapped")
