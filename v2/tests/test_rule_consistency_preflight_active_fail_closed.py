#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_rule_consistency_preflight_active.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("rule consistency independent review baseline failed")
cases=[
 ("skip-authority",lambda d:d["requirements"].update({"github_current_authority_must_be_checked":False}),"preflight guard invalid"),
 ("allow-chat-only",lambda d:d["requirements"].update({"chat_memory_alone_forbidden":False}),"preflight guard invalid"),
 ("drop-prior",lambda d:d["requirements"]["required_preflight_sources"].remove("applicable prior rule versions"),"preflight source missing"),
 ("drop-conflict-decision",lambda d:d["requirements"]["required_decisions"].remove("conflict"),"preflight decision missing"),
 ("allow-conflict",lambda d:d["requirements"].update({"unresolved_conflict_blocks_rule_progression":False}),"preflight guard invalid"),
 ("self-active",lambda d:d.update({"status":"CANDIDATE"}),"active identity/status invalid")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/rule_consistency_preflight_active.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected rule-consistency rejection:",name)
print("PASS rule consistency preflight destructive cases rejected")
