#!/usr/bin/env python3
"""Candidate-only evidence preflight. No authorization or release PASS is issued."""
import json
import pathlib
import sys

MANDATORY = ("basis_head", "target_head", "change_id", "planned_paths",
             "actual_pr_paths", "approval", "research", "tests", "review",
             "checks", "apk", "device", "branch_protection")
def validate(e):
    errors = []
    if not isinstance(e, dict):
        return ["evidence must be an object"]
    for k in MANDATORY:
        if k not in e:
            errors.append("missing " + k)
    if errors:
        return errors
    if not all(isinstance(e.get(k), str) and len(e[k]) == 40 and
               all(c in "0123456789abcdef" for c in e[k]) for k in ("basis_head", "target_head")):
        errors.append("invalid HEAD SHA")
    paths = e["planned_paths"]
    actual = e["actual_pr_paths"]
    if not isinstance(paths, list) or not isinstance(actual, list) or not paths or not actual:
        errors.append("missing planned/actual paths")
    elif not set(actual).issubset(set(paths)):
        errors.append("actual PR diff outside approved paths")
    a = e["approval"]
    if not isinstance(a, dict) or a.get("change_id") != e["change_id"] or a.get("basis_head") != e["basis_head"]:
        errors.append("approval binding mismatch")
    # A self-authored record or PR text cannot establish real user consent.
    errors.append("approval authenticity requires independent trusted user evidence")
    for k in ("research", "tests", "review", "checks", "apk", "device"):
        v = e[k]
        if not isinstance(v, dict) or v.get("verified") is not True or not v.get("evidence_refs"):
            errors.append(k + " missing independent evidence")
    if e["checks"].get("head_sha") != e["target_head"]:
        errors.append("CI HEAD mismatch")
    if e["branch_protection"] is not True:
        errors.append("branch protection unverified")
    if e.get("completion") is True and e["device"].get("verified") is not True:
        errors.append("device acceptance missing")
    return errors

def main(argv):
    if len(argv) != 2:
        print("BLOCKED: candidate requires a local evidence JSON; never infer approval")
        return 2
    p = pathlib.Path(argv[1])
    if not p.is_file():
        print("BLOCKED: evidence file missing")
        return 2
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        errors = validate(data)
    except (ValueError, OSError, TypeError, AttributeError) as ex:
        print("BLOCKED: malformed evidence:", ex)
        return 2
    for err in errors:
        print("BLOCKED:", err)
    if errors:
        return 1
    # Deliberately unreachable until independent approval verifier is implemented.
    print("CANDIDATE PREFLIGHT PASS (not release authorization)")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
