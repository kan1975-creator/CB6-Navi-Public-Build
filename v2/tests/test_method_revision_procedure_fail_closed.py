#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_method_revision_procedure.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
b=run(S)
if b.returncode: raise SystemExit("method revision procedure baseline failed\n"+b.stdout+b.stderr)
cases=[
 ("allow-hash-rewrite",lambda d:d["invariants"].update({"direct_freeze_hash_rewrite_forbidden":False}),"direct_freeze_hash_rewrite_forbidden"),
 ("allow-self-adoption",lambda d:d["invariants"].update({"candidate_cannot_verify_its_own_adoption":False}),"candidate_cannot_verify_its_own_adoption"),
 ("drop-independent-review",lambda d:d.update({"required_sequence":[x for x in d["required_sequence"] if x!="perform_independent_review_against_prechange_authority_and_candidate"]}),"revision sequence incomplete"),
 ("drop-user-adoption",lambda d:d.update({"required_sequence":[x for x in d["required_sequence"] if x!="obtain_explicit_user_adoption"]}),"revision sequence incomplete")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/method_revision_procedure_v1.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d))
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected method-revision rejection:",name)
print("PASS method revision procedure destructive cases rejected")
