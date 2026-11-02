#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXED_COMMIT = "b1f139b7826a00b777ac9f728799cf02aa9637d1"

def read_file_content(rel_path):
    p = ROOT / rel_path
    if p.is_file():
        return p.read_text(encoding="utf-8")
    cmd = ["git", "show", f"{FIXED_COMMIT}:{rel_path}"]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode == 0:
        return res.stdout
    return None

def main():
    reg_text = read_file_content("v2/gates/operational_rule_registry_v22_candidate.json")
    cov_text = read_file_content("v2/gates/rule_coverage.json")

    if not reg_text:
        print("CB6 RULE COVERAGE V4 CANDIDATE FAIL: missing registry")
        raise SystemExit(1)
    if not cov_text:
        print("CB6 RULE COVERAGE V4 CANDIDATE FAIL: missing coverage")
        raise SystemExit(1)

    reg = json.loads(reg_text)
    cov = json.loads(cov_text)

    active = {x["id"] for x in reg["rules"] if x.get("status") == "ACTIVE"}
    proposed = {x["id"] for x in reg["rules"] if x.get("status") == "PROPOSED"}
    covered = {x["rule_id"] for x in cov["entries"]}

    errors = []
    for x in sorted(active - covered):
        errors.append("ACTIVE registry rule missing from coverage: " + x)
    for x in sorted(covered - active):
        errors.append("coverage rule missing from registry: " + x)
    for x in sorted(proposed & covered):
        errors.append("PROPOSED rule must not enter active coverage: " + x)

    if "OPS-GOV-R36-CONSOLIDATED-001" not in proposed:
        errors.append("PROPOSED candidate rule OPS-GOV-R36-CONSOLIDATED-001 missing from v22 candidate registry")

    if errors:
        print("CB6 RULE COVERAGE V4 CANDIDATE FAIL:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)

    print(f"CB6 RULE COVERAGE V4 CANDIDATE PASS: active={len(active)}; proposed={len(proposed)}; machine_enforced={len(covered)}; candidate_r36_tracked=1")

if __name__ == "__main__":
    main()
