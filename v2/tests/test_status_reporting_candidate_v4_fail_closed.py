#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[2]; CMD=["python3","v2/gates/verify_status_reporting_candidate_v4.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
if run(S).returncode: raise SystemExit("status reporting v4 candidate baseline failed")
cases=[
 ("four-lines-not-final",lambda d:d["four_line_template"].update({"placement":"ANYWHERE"}),"final four-line placement invalid"),
 ("four-lines-reordered",lambda d:d["four_line_template"].update({"order_exactly_required":["分類","ChatGPTアプリ","次にユーザーがすること","スマホ操作"]}),"final four-line placement invalid"),
 ("allow-content-after-four-lines",lambda d:d["four_line_template"].update({"content_after_four_lines_forbidden":False}),"final four-line placement invalid"),
 ("drop-final-section",lambda d:d["rules"]["スマホ操作が必要"]["required_fields"].remove("final_user_action_section"),"smartphone required field missing"),
 ("wrong-heading",lambda d:d["rules"]["スマホ操作が必要"]["final_user_action_section"].update({"heading":"スマホ操作"}),"final user action section invalid"),
 ("not-at-end",lambda d:d["rules"]["スマホ操作が必要"]["final_user_action_section"].update({"placement":"ANYWHERE"}),"final user action section invalid"),
 ("allow-generic",lambda d:d["rules"]["スマホ操作が必要"]["final_user_action_section"].update({"generic_device_instruction_forbidden":False}),"final user action section invalid"),
 ("disable-fail-closed",lambda d:d["rules"]["スマホ操作が必要"]["fail_closed"].update({"required":False}),"smartphone fail-closed rule invalid"),
 ("allow-unidentified",lambda d:d["rules"]["スマホ操作が必要"]["fail_closed"].update({"if_concrete_operation_not_identified":"ALLOW"}),"smartphone fail-closed rule invalid")]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_candidate_v4.json"; d=json.loads(p.read_text()); mut(d); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting-v4 rejection:",name)
print("PASS status reporting v4 candidate destructive cases rejected")
