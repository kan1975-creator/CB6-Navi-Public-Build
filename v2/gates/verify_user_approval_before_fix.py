#!/usr/bin/env python3
"""CB6 approval verifier. Stage 1: not wired to an enforcement gate."""
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / "v2/gates/user_approval_before_fix_contract.json").read_text())
FIELDS = CONTRACT["stage1"]["canonical_plan_fields"]
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def instant(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be UTC RFC3339")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset().total_seconds() != 0:
        raise ValueError("timestamp not UTC")
    return result

def plan_digest(plan):
    if not isinstance(plan, dict) or any(k not in plan for k in FIELDS):
        raise ValueError("incomplete canonical plan")
    data = {k: plan[k] for k in FIELDS}
    if not isinstance(data["proposed_change_id"], str) or not data["proposed_change_id"]:
        raise ValueError("invalid change id")
    if not isinstance(data["basis_head"], str) or not SHA.fullmatch(data["basis_head"]):
        raise ValueError("invalid basis head")
    for k in ("planned_paths", "forbidden_scope", "affected_domains"):
        if not isinstance(data[k], list) or not all(isinstance(x, str) and x for x in data[k]):
            raise ValueError("invalid scope")
        if len(set(data[k])) != len(data[k]):
            raise ValueError("duplicate scope")
        data[k] = sorted(data[k])
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def check(d, github_comment=None, trusted=None):
    """Fail-closed evidence validation. No caller-supplied API result is production authority."""
    errors = []
    if not isinstance(d, dict):
        return ["invalid evidence"]
    approval = d.get("approval")
    if not isinstance(approval, dict):
        return ["missing approval"]
    for field in CONTRACT["approval_record"]["required_fields"]:
        if not approval.get(field):
            errors.append("missing approval field: " + field)
    if approval.get("proposed_change_id") != d.get("proposed_change_id"):
        errors.append("approval binding mismatch")
    if not approval.get("github_reference"):
        errors.append("missing github approval reference")
    if not isinstance(trusted, dict) or not isinstance(github_comment, dict):
        return errors + ["trusted GitHub evidence missing"]
    try:
        plan = trusted["plan"]
        digest = plan_digest(plan)
        if digest != trusted["plan_sha256"] or not DIGEST.fullmatch(trusted["plan_sha256"]):
            errors.append("plan hash mismatch")
        if plan["proposed_change_id"] != d.get("proposed_change_id"):
            errors.append("plan change binding mismatch")
        if plan["basis_head"] != trusted["basis_head"] or plan["basis_head"] != d.get("basis_head"):
            errors.append("basis HEAD mismatch")
        if not SHA.fullmatch(trusted["plan_commit_sha"]):
            errors.append("invalid plan commit")
        if github_comment["user"]["id"] != CONTRACT["stage1"]["trusted_github_user_id"]:
            errors.append("GitHub user mismatch")
        if github_comment["id"] != trusted["comment_id"]:
            errors.append("comment ID mismatch")
        if github_comment.get("created_at") != github_comment.get("updated_at"):
            errors.append("edited comment")
        created = instant(github_comment["created_at"])
        started = instant(trusted["implementation_event_at"])
        if created >= started:
            errors.append("approval is not pre-implementation")
        if approval.get("approved_at") != github_comment["created_at"]:
            errors.append("approval timestamp mismatch")
        body = github_comment["body"]
        expected = ("CB6-APPROVE " + plan["proposed_change_id"] + " " +
                    trusted["plan_sha256"] + " " + trusted["plan_commit_sha"])
        if not isinstance(body, str) or body.strip() != expected:
            errors.append("approval comment content mismatch")
        if approval.get("github_reference") != ("issue-comment:" + str(trusted["comment_id"])):
            errors.append("approval reference mismatch")
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        errors.append("invalid trusted evidence: " + str(exc))
    return errors

def github_get(repo, endpoint, token):
    if not REPO.fullmatch(repo) or not token:
        raise ValueError("invalid GitHub API configuration")
    req = urllib.request.Request(
        "https://api.github.com/repos/" + repo + endpoint,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)

def verify_live(d, trusted, token, fetch=github_get):
    """Production: obtain both comment and plan blob from GitHub, never from supplied mock."""
    try:
        if not isinstance(trusted, dict):
            return ["trusted configuration missing"]
        repo = trusted["repository"]
        comment_id = trusted["comment_id"]
        commit = trusted["plan_commit_sha"]
        path = trusted["plan_path"]
        if not isinstance(comment_id, int) or comment_id <= 0:
            raise ValueError("invalid comment id")
        if not isinstance(commit, str) or not SHA.fullmatch(commit):
            raise ValueError("invalid plan commit")
        if not isinstance(path, str) or not path or ".." in path.split("/") or path.startswith("/"):
            raise ValueError("invalid plan path")
        comment = fetch(repo, "/issues/comments/" + str(comment_id), token)
        obj = fetch(repo, "/contents/" + path + "?ref=" + commit, token)
        import base64
        if obj.get("encoding") != "base64" or obj.get("type") != "file":
            raise ValueError("invalid plan blob")
        raw = base64.b64decode(obj["content"], validate=False)
        plan = json.loads(raw.decode("utf-8"))
        bound = dict(trusted)
        bound["plan"] = plan
        return check(d, comment, bound)
    except (OSError, urllib.error.URLError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return ["GitHub API or plan retrieval failed: " + str(exc)]

def main(argv):
    if len(argv) != 3:
        print("usage: verify_user_approval_before_fix.py evidence.json trusted-config.json")
        return 1
    try:
        evidence = json.loads(Path(argv[1]).read_text())
        trusted = json.loads(Path(argv[2]).read_text())
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN missing")
        errors = verify_live(evidence, trusted, token)
    except (OSError, ValueError, TypeError) as exc:
        errors = ["configuration failure: " + str(exc)]
    if errors:
        print("CB6 PRE-FIX USER APPROVAL FAIL:", *errors, sep="\n - ")
        return 1
    print("CB6 PRE-FIX USER APPROVAL PASS: live GitHub evidence verified; ENFORCEMENT_UNVERIFIED")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
