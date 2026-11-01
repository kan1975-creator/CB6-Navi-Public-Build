#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def run_step(cmd, name):
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"CB6 PROJECT GATE V22 CANDIDATE FAIL at {name}:")
        print(res.stdout)
        print(res.stderr)
        raise SystemExit(1)
    print(f" - {name}: PASS")

def main():
    print("CB6 PROJECT GATE V22 CANDIDATE EXECUTION:")
    # Step 1: Candidate v22 Operational Rule Registry & R36 Verifier
    run_step([sys.executable, "v2/gates/verify_governance_r36_candidate.py"], "v22 Candidate R36 Verifier")
    # Step 2: Candidate v4 Rule Coverage
    run_step([sys.executable, "v2/gates/verify_rule_coverage_v4_candidate.py"], "v22 Candidate Rule Coverage")
    
    print("CB6 PROJECT GATE V22 CANDIDATE COMPLETE: ALL CANDIDATE CHECKS PASSED.")

if __name__ == "__main__":
    main()
