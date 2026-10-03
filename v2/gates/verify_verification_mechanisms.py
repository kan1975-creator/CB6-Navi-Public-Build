#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];d=json.loads((R/"v2/gates/verification_mechanisms.json").read_text());e=[]
ids=[x["id"] for x in d["mechanisms"]]
if len(ids)!=len(set(ids)):e.append("duplicate mechanism id")
for x in d["mechanisms"]:
 if not (R/x["authority"]).exists():e.append("missing authority: "+x["authority"])
if e: print("CB6 MECHANISM CATALOG FAIL:\n - "+"\n - ".join(e));raise SystemExit(1)
print(f"CB6 MECHANISM CATALOG PASS: mechanisms={len(ids)}; missing=0; duplicate_ids=0")
