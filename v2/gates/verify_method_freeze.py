#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/"v2/gates/method_freeze_lock.json"
def fail(m):
    print("CB6 METHOD FREEZE FAIL:",m); raise SystemExit(1)
if not LOCK.is_file(): fail("freeze lock missing")
d=json.loads(LOCK.read_text(encoding="utf-8"))
if d.get("schema")!=1 or d.get("status")!="FROZEN": fail("method is not frozen")
files=d.get("files",{})
if not isinstance(files,dict) or not files: fail("freeze file set empty")
for rel,expected in files.items():
    p=ROOT/rel
    if not p.is_file(): fail("frozen method file missing: "+rel)
    b=p.read_bytes(); actual=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    if actual!=expected: fail("frozen method file changed: "+rel)
print("CB6 METHOD FREEZE PASS:",len(files),"files unchanged")
