#!/usr/bin/env python3
import subprocess
def r(args,needle,code):
 p=subprocess.run(["python3","v2/gates/classify_gate_result.py"]+args,text=True,capture_output=True)
 if p.returncode!=code or needle not in p.stdout:raise SystemExit(p.stdout+p.stderr)
 print("PASS gate-result classification:",p.stdout.strip())
r(["--freeze-failed"],"EXPECTED_FREEZE_FAIL",0)
r(["--unexpected-failures","1"],"UNEXPECTED_FAIL",1)
