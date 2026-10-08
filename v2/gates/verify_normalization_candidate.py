#!/usr/bin/env python3
"""Read-only GitHub evidence audit. Candidate audit success is NOT release approval."""
import json
import os
import sys
import urllib.error
import urllib.request

ALLOWED = frozenset({
    "docs/CB6_NORMALIZATION_CANDIDATE.md",
    "v2/gates/verify_normalization_candidate.py",
    "v2/tests/test_normalization_candidate_fail_closed.py",
    ".github/workflows/cb6_normalization_candidate.yml",
})
REQUIRED_CHECKS = {"CB6 Development Gate", "CB6 Governance Normalization Candidate"}

def audit(snapshot, expected_head, expected_base):
    """Verify independently fetched GitHub facts, return explicit blockers."""
    blockers = []
    if not isinstance(snapshot, dict):
        return ["malformed GitHub evidence"]
    pr, files, reviews, runs, branch = (snapshot.get(k) for k in
        ("pr", "files", "reviews", "runs", "branch"))
    if not isinstance(pr, dict) or not isinstance(files, list) or not isinstance(reviews, list) or not isinstance(runs, list) or not isinstance(branch, dict):
        return ["missing GitHub API evidence"]
    head = (pr.get("head") or {}).get("sha") if isinstance(pr.get("head"), dict) else None
    base = (pr.get("base") or {}).get("sha") if isinstance(pr.get("base"), dict) else None
    if head != expected_head or base != expected_base or branch.get("commit", {}).get("sha") != expected_base:
        blockers.append("stale or mismatched GitHub HEAD")
    if pr.get("state") != "open" or pr.get("draft") is not True:
        blockers.append("candidate PR must remain open and draft")
    names = [x.get("filename") for x in files if isinstance(x, dict)]
    if len(names) != len(files) or set(names) != ALLOWED or len(names) != len(set(names)) or any(x.get("status") != "modified" for x in files):
        blockers.append("actual GitHub PR diff outside approved four modified files")
    if branch.get("protected") is not True:
        blockers.append("branch protection not enabled")
    # Never trust review summaries or a self-authored PR body.
    valid_reviews = [x for x in reviews if isinstance(x, dict) and x.get("state") == "APPROVED" and
        x.get("commit_id") == expected_head and
        (x.get("user") or {}).get("login") != (pr.get("user") or {}).get("login")]
    if not valid_reviews:
        blockers.append("independent GitHub review missing")
    for name in REQUIRED_CHECKS:
        matching = [x for x in runs if isinstance(x, dict) and x.get("name") == name and
            x.get("head_sha") == expected_head and x.get("status") == "completed" and x.get("conclusion") == "success"]
        if not matching:
            blockers.append("missing current-SHA CI: " + name)
    # Approval in this chat cannot be authenticated by GitHub API; no automatic bypass.
    blockers.append("user approval authenticity not independently verifiable")
    blockers.append("APK provenance and CB6 device acceptance not verified")
    return blockers

def github(path):
    api = "https://api.github.com/repos/kan1975-creator/CB6-Navi-Public-Build"
    req = urllib.request.Request(api + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def fetch_snapshot(pr_number):
    pr = github("/pulls/" + str(pr_number))
    branch_name = pr["base"]["ref"]
    files = github("/pulls/" + str(pr_number) + "/files?per_page=100")
    if len(files) >= 100 or pr.get("changed_files") != len(files):
        raise ValueError("PR file pagination incomplete")
    reviews = github("/pulls/" + str(pr_number) + "/reviews?per_page=100")
    if len(reviews) >= 100:
        raise ValueError("review pagination incomplete")
    runs_data = github("/actions/runs?head_sha=" + pr["head"]["sha"] + "&per_page=100")
    if runs_data.get("total_count", 0) > len(runs_data.get("workflow_runs", [])):
        raise ValueError("workflow runs pagination incomplete")
    return {"pr": pr, "files": files, "reviews": reviews,
            "runs": runs_data["workflow_runs"], "branch": github("/branches/" + branch_name)}

def main():
    if len(sys.argv) != 4 or not os.environ.get("GITHUB_TOKEN"):
        print("BLOCKED: PR number, expected head/base, and GitHub token required")
        return 2
    try:
        snapshot = fetch_snapshot(int(sys.argv[1]))
        blockers = audit(snapshot, sys.argv[2], sys.argv[3])
    except (ValueError, KeyError, TypeError, urllib.error.URLError, OSError) as ex:
        print("BLOCKED: GitHub evidence unavailable:", ex)
        return 2
    for blocker in blockers:
        print("BLOCKED:", blocker)
    # Exit 0 means audit executed and known safety blockers remained blocked.
    # This is NOT a release check or an approval gate.
    if not blockers:
        print("ERROR: candidate audit unexpectedly has no blockers")
        return 1
    print("PASS: read-only candidate audit ran; release remains BLOCKED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
