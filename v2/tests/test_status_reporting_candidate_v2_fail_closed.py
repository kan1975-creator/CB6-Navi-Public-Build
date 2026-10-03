#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v2.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("v2 candidate baseline failed")
with tempfile.TemporaryDirectory() as td:
 r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
 p=r/"v2/gates/status_reporting_contract_candidate_v2.json"; d=json.loads(p.read_text())
 d["rules"]["待ち"]["post_wait_user_instruction"]["required"]=False
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 cp=run(r); out=cp.stdout+cp.stderr
 if cp.returncode==0 or "post-wait instruction invalid" not in out: raise SystemExit("missing post-wait instruction was not rejected\n"+out)
print("PASS: v2 candidate fails closed when post-wait instruction requirement is removed")
