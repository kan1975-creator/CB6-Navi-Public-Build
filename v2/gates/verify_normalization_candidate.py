#!/usr/bin/env python3
"""Candidate-only, read-only GitHub evidence audit; never authorizes release."""
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
# Only the pre-existing independent Development Gate is eligible here.
# Candidate workflow cannot verify its own success while still running.
REQUIRED_CHECKS = {"CB6 Development Gate"}

def audit(snapshot, expected_head, expected_base):
    """Return (audit_errors, release_blockers). Neither is release authorization."""
    errors, blockers = [], []
    if not isinstance(snapshot, dict):
        return ["malformed GitHub evidence"], []
    pr, files, reviews, runs, branch = (snapshot.get(k) for k in
        ("pr", "files", "reviews", "runs", "branch"))
    if not isinstance(pr, dict) or not isinstance(files, list) or not isinstance(reviews, list) or not isinstance(runs, list) or not isinstance(branch, dict):
        return ["missing GitHub API evidence"], []
    head, base = pr.get("head"), pr.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict) or not isinstance(branch.get("commit"), dict):
        return ["malformed PR or branch evidence"], []
    if head.get("sha") != expected_head or base.get("sha") != expected_base or branch["commit"].get("sha") != expected_base:
        errors.append("stale or mismatched GitHub HEAD")
    if pr.get("state") != "open" or pr.get("draft") is not True:
        blockers.append("candidate PR must remain open and draft")
    if any(not isinstance(x, dict) for x in files):
        errors.append("malformed PR files")
    else:
        names = [x.get("filename") for x in files]
        if set(names) != ALLOWED or len(names) != len(ALLOWED) or any(x.get("status") != "added" for x in files):
            errors.append("actual GitHub PR diff outside approved four added files")
    # Branch protection is advisory here; ACTIVE authority must be checked separately.
    author = (pr.get("user") or {}).get("login") if isinstance(pr.get("user"), dict) else None
    # GitHub review records are chronological. Latest decisive state per reviewer wins.
    latest = {}
    for review in reviews:
        if not isinstance(review, dict) or not isinstance(review.get("user"), dict):
            errors.append("malformed review evidence")
            continue
        login = review["user"].get("login")
        if not isinstance(login, str) or not login:
            errors.append("malformed reviewer identity")
            continue
        if login != author:
            latest[login] = review
    approvals = [v for v in latest.values() if v.get("state") == "APPROVED" and v.get("commit_id") == expected_head]
    changes = [v for v in latest.values() if v.get("state") == "CHANGES_REQUESTED"]
    # GitHub approval is supporting evidence, not the sole independent-review route.
    if changes:
        blockers.append("unresolved changes requested")
    threads = snapshot.get("review_threads")
    if not isinstance(threads, list):
        blockers.append("review-thread resolution not independently verified")
    elif any(not isinstance(t, dict) or not isinstance(t.get("isResolved"), bool) for t in threads):
        errors.append("malformed review-thread evidence")
    elif any(not t["isResolved"] for t in threads):
        blockers.append("unresolved review threads")
    # Independent automated review and human GitHub review are distinct evidence.
    independent = [x for x in runs if isinstance(x, dict) and
        x.get("name") == "CB6 Governance Normalization Independent Review" and
        x.get("head_sha") == expected_head and x.get("status") == "completed" and
        x.get("conclusion") == "success"]
    # A named workflow alone cannot establish separate review context.
    # The four-file documentation/audit candidate is not an APK or device release.
    # This does not waive acceptance for a later application release.
    if set(x.get("filename") for x in files if isinstance(x, dict)) != ALLOWED:
        blockers.append("APK provenance and CB6 device acceptance not verified")
    for name in REQUIRED_CHECKS:
        matches = [x for x in runs if isinstance(x, dict) and x.get("name") == name and
            x.get("head_sha") == expected_head and x.get("status") == "completed" and x.get("conclusion") == "success"]
        if not matches:
            blockers.append("missing current-SHA CI: " + name)
    blockers.append("ACTIVE pre-fix approval binding and timing not independently verified")
    blockers.append("ACTIVE independent review context, target SHA and evidence not independently verified")
    return errors, blockers

def github(path):
    api = "https://api.github.com/repos/kan1975-creator/CB6-Navi-Public-Build"
    req = urllib.request.Request(api + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def fetch_review_threads(pr_number):
    """GitHub GraphQL provides the authoritative resolved state of PR threads."""
    query = """query($owner:String!,$repo:String!,$number:Int!){
      repository(owner:$owner,name:$repo){
        pullRequest(number:$number){
          reviewThreads(first:100){nodes{isResolved} pageInfo{hasNextPage}}
        }
      }
    }"""
    payload = json.dumps({"query": query, "variables": {
        "owner": "kan1975-creator", "repo": "CB6-Navi-Public-Build",
        "number": pr_number}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=payload, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.load(response)
    if data.get("errors"):
        raise ValueError("GraphQL review-thread query errors")
    try:
        threads = data["data"]["repository"]["pullRequest"]["reviewThreads"]
        if threads["pageInfo"]["hasNextPage"]:
            raise ValueError("review-thread pagination incomplete")
        return threads["nodes"]
    except (KeyError, TypeError) as exc:
        raise ValueError("malformed review-thread API response") from exc

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
            "review_threads": fetch_review_threads(pr_number),
            "runs": runs_data["workflow_runs"], "branch": github("/branches/" + branch_name)}

def main():
    if len(sys.argv) != 4 or not os.environ.get("GITHUB_TOKEN"):
        print("AUDIT_ERROR: PR number, expected SHA values and GitHub token required")
        return 2
    try:
        snapshot = fetch_snapshot(int(sys.argv[1]))
        errors, blockers = audit(snapshot, sys.argv[2], sys.argv[3])
    except (ValueError, KeyError, TypeError, AttributeError, urllib.error.URLError, OSError) as ex:
        print("AUDIT_ERROR: GitHub evidence unavailable:", ex)
        return 2
    for issue in errors:
        print("AUDIT_ERROR:", issue)
    for issue in blockers:
        print("RELEASE_BLOCKED:", issue)
    if errors:
        return 2
    # Advisory candidate job succeeds only when evidence was read consistently.
    # Release remains blocked, irrespective of this exit code.
    print("AUDIT_OK: evidence audit completed; RELEASE_BLOCKED remains")
    return 0

if __name__ == "__main__":
    sys.exit(main())
