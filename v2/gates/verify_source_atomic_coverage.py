#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def fail(msg):
    print("CB6 SOURCE-ATOMIC COVERAGE FAIL:",msg); raise SystemExit(1)
cov=json.loads((ROOT/"v2/gates/source_atomic_coverage.json").read_text(encoding="utf-8"))
atomic=json.loads((ROOT/"v2/gates/atomic_requirements.json").read_text(encoding="utf-8"))
if cov.get("status")!="COMPLETE": fail("coverage status is not COMPLETE")
sources=cov.get("sources",[])
if not sources: fail("source corpus empty")
for s in sources:
    if not (ROOT/s.get("path","")).is_file(): fail("source missing: "+str(s.get("path")))
    if s.get("coverage")!="COMPLETE": fail("source coverage incomplete: "+s.get("path","?"))
clauses=cov.get("clause_coverage",[])
if not clauses: fail("clause coverage empty")
valid_classes={"ACTIVE_REQUIREMENT","SUPERSEDED","HISTORICAL_ONLY","RETIRED","REVALIDATION_REQUIRED","NON_REQUIREMENT"}
atomic_ids={r.get("id") for r in atomic.get("requirements",[])}
mapped=set()
seen=set()
for c in clauses:
    key=(c.get("source"),c.get("clause_id"))
    if not all(key) or key in seen: fail("invalid/duplicate clause identity: "+repr(key))
    seen.add(key)
    if c.get("classification") not in valid_classes: fail("unknown/unmapped clause: "+repr(key))
    ids=c.get("atomic_ids",[])
    if c["classification"]=="ACTIVE_REQUIREMENT" and not ids: fail("active clause has no atomic mapping: "+repr(key))
    for rid in ids:
        if rid not in atomic_ids: fail("clause maps missing atomic id: "+rid)
        mapped.add(rid)
missing=atomic_ids-mapped
if missing: fail("atomic requirements without clause provenance: "+",".join(sorted(missing)[:20]))
print("CB6 SOURCE-ATOMIC COVERAGE PASS:",len(sources),"sources",len(clauses),"clauses",len(mapped),"atomic requirements")
