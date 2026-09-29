#!/usr/bin/env python3
import argparse
p=argparse.ArgumentParser();p.add_argument("--freeze-failed",action="store_true");p.add_argument("--unexpected-failures",type=int,default=0);a=p.parse_args()
if a.unexpected_failures: print(f"UNEXPECTED_FAIL: count={a.unexpected_failures}");raise SystemExit(1)
if a.freeze_failed: print("EXPECTED_FREEZE_FAIL: method reconstruction changed frozen authority; re-freeze required");raise SystemExit(0)
print("PASS: no classified failures")
