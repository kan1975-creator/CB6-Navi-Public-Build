#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[2]
CMD=["python3","v2/gates/verify_status_reporting_candidate.py"]
def run(r): return subprocess.run(CMD,cwd=r,text=True,capture_output=True)
b=run(S)
if b.returncode: raise SystemExit("status reporting candidate baseline failed\n"+b.stdout+b.stderr)
cases=[
 ("fourth-class",lambda d:d["allowed_classifications"].append("その他"),"classification set/order drifted"),
 ("not-exactly-one",lambda d:d.update({"exactly_one_classification_required":False}),"exactly-one classification not required"),
 ("wait-missing-field",lambda d:d["rules"]["待ち"].update({"required_fields":["approximate_wait_time","next_check_timing"]}),"wait fields invalid"),
 ("device-missing-evidence",lambda d:d["rules"]["スマホ操作が必要"].update({"required_fields":["required_device_action"]}),"device fields invalid"),
 ("stale-weakened",lambda d:d["freshness_rule"].update({"progress_query_requires_current_head":False}),"freshness weakened"),
 ("generic-progress-is-fix-approval",lambda d:d["fix_approval_boundary"].update({"generic_progress_permission_is_not_specific_fix_approval":False}),"fix approval boundary invalid"),
 ("direct-active",lambda d:d["activation"].update({"direct_active_forbidden":False}),"direct activation allowed")
]
for name,mut,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  r=Path(td)/"repo"; shutil.copytree(S,r,ignore=shutil.ignore_patterns(".git","out","comaps"))
  p=r/"v2/gates/status_reporting_contract_candidate_v1.json"; d=json.loads(p.read_text(encoding="utf-8")); mut(d); p.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
  cp=run(r); out=cp.stdout+cp.stderr
  if cp.returncode==0 or needle not in out: raise SystemExit(name+" not rejected\n"+out)
  print("PASS expected status-reporting rejection:",name)
print("PASS status-reporting destructive cases rejected")
