#!/usr/bin/env python3
"""CB6 approval verifier; production stays blocked without protected provenance."""
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import quote
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
    """Synthetic compatibility check only; caller data is not production authority."""
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
        expected_issue = "https://api.github.com/repos/" + trusted["repository"] + "/issues/" + str(trusted["issue_number"])
        if github_comment.get("issue_url") != expected_issue:
            errors.append("issue ownership mismatch")
        if github_comment.get("created_at") != github_comment.get("updated_at"):
            errors.append("edited comment")
        created = instant(github_comment["created_at"])
        started = instant(trusted["implementation_event_at"])
        if not trusted.get("implementation_event_verified"):
            errors.append("implementation event not independently verified")
        if not trusted.get("plan_anchor_verified"):
            errors.append("plan anchor not independently verified")
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

def _verify_with_transport(d, trusted, token, fetch):
    """Synthetic transport test: validates fetched comment/plan, not trust origin."""
    try:
        if not isinstance(trusted, dict):
            return ["trusted configuration missing"]
        repo = trusted["repository"]
        comment_id = trusted["comment_id"]
        commit = trusted["plan_commit_sha"]
        path = trusted["plan_path"]
        issue_number = trusted["issue_number"]
        if not isinstance(issue_number, int) or isinstance(issue_number, bool) or issue_number <= 0:
            raise ValueError("invalid issue number")
        if not isinstance(comment_id, int) or comment_id <= 0:
            raise ValueError("invalid comment id")
        if not isinstance(commit, str) or not SHA.fullmatch(commit):
            raise ValueError("invalid plan commit")
        if not isinstance(path, str) or not path or ".." in path.split("/") or path.startswith("/"):
            raise ValueError("invalid plan path")
        comment = fetch(repo, "/issues/comments/" + str(comment_id), token)
        obj = fetch(repo, "/contents/" + quote(path, safe="/") + "?ref=" + commit, token)
        commit_obj = fetch(repo, "/commits/" + commit, token)
        if commit_obj.get("sha") != commit:
            raise ValueError("plan commit SHA mismatch")
        if not commit_obj.get("commit", {}).get("committer", {}).get("date"):
            raise ValueError("plan commit timestamp missing")
        if instant(commit_obj["commit"]["committer"]["date"]) >= instant(comment["created_at"]):
            raise ValueError("plan commit is not before approval (metadata check only)")
        import base64
        if obj.get("encoding") != "base64" or obj.get("type") != "file":
            raise ValueError("invalid plan blob")
        encoded = obj["content"]
        if not isinstance(encoded, str):
            raise ValueError("invalid base64 plan content")
        # GitHub may fold base64 with CR/LF; other invalid characters still reject.
        raw = base64.b64decode(encoded.replace("\r", "").replace("\n", ""), validate=True)
        plan = json.loads(raw.decode("utf-8"))
        bound = dict(trusted)
        bound["plan"] = plan
        return check(d, comment, bound)
    except (OSError, urllib.error.URLError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return ["GitHub API or plan retrieval failed: " + str(exc)]

def verify_pr_diff_with_transport(d, trusted, token, fetch):
    """Read-only PR scope audit, TEST HELPER; never grants production approval.

    Recheck head/base before and after listing all changes. Caller-controlled
    planned_paths alone is not an independently trusted plan. An actual gate
    must establish plan provenance separately before this audit can be used.
    """
    try:
        if not isinstance(d, dict) or not isinstance(trusted, dict):
            raise ValueError("missing PR evidence")
        repo = trusted["repository"]
        pr_number = trusted["pr_number"]
        expected_head = trusted["pr_head_sha"]
        expected_base = trusted["pr_base_sha"]
        expected_base_ref = trusted["pr_base_ref"]
        plan = trusted["plan"]
        if not isinstance(repo, str) or not REPO.fullmatch(repo):
            raise ValueError("invalid PR repository")
        if type(pr_number) is not int or pr_number <= 0:
            raise ValueError("invalid PR number")
        if not isinstance(expected_head, str) or not SHA.fullmatch(expected_head):
            raise ValueError("invalid PR HEAD")
        if not isinstance(expected_base, str) or not SHA.fullmatch(expected_base):
            raise ValueError("invalid PR base HEAD")
        if (not isinstance(expected_base_ref, str) or
                not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", expected_base_ref) or
                any(part in (".", "..") for part in expected_base_ref.split("/"))):
            raise ValueError("invalid PR base ref")
        # Validates shape/duplicate paths, not authenticity of proposed plan.
        plan_digest(plan)
        if plan["proposed_change_id"] != d.get("proposed_change_id"):
            raise ValueError("PR change binding mismatch")
        if plan["basis_head"] != expected_base or d.get("basis_head") != expected_base:
            raise ValueError("PR basis HEAD mismatch")
        def get_pr():
            x = fetch(repo, "/pulls/" + str(pr_number), token)
            if not isinstance(x, dict) or x.get("number") != pr_number:
                raise ValueError("PR identity mismatch")
            if x.get("state") != "open":
                raise ValueError("PR not open")
            if x.get("head", {}).get("sha") != expected_head:
                raise ValueError("PR HEAD mismatch")
            if x.get("base", {}).get("sha") != expected_base:
                raise ValueError("PR base HEAD mismatch")
            if x.get("base", {}).get("ref") != expected_base_ref:
                raise ValueError("PR base ref mismatch")
            if x.get("base", {}).get("repo", {}).get("full_name") != repo:
                raise ValueError("PR repository mismatch")
            count = x.get("changed_files")
            if type(count) is not int or not (0 < count <= 300):
                raise ValueError("unsupported PR changed file count")
            return count
        before = get_pr()
        changed = []
        touched = []  # Both rename endpoints must be explicitly within the approved plan.
        for page in range(1, 1 + ((before + 99) // 100)):
            files = fetch(repo, "/pulls/" + str(pr_number)
                          + "/files?per_page=100&page=" + str(page), token)
            if not isinstance(files, list) or not (1 <= len(files) <= 100):
                raise ValueError("PR file page missing")
            for item in files:
                if not isinstance(item, dict) or not isinstance(item.get("filename"), str):
                    raise ValueError("malformed PR file")
                path = item["filename"]
                def safe_path(value):
                    return (isinstance(value, str) and bool(value) and
                            not value.startswith("/") and "\\" not in value and
                            all(part not in ("", ".", "..") for part in value.split("/")))
                if not safe_path(path):
                    raise ValueError("unsafe PR path")
                status = item.get("status")
                # Every GitHub PR file needs an explicit supported status.
                # Caller-supplied synthetic fixtures have no production exception.
                if status not in ("added", "modified", "removed", "renamed"):
                    raise ValueError("missing or unsupported PR file status")
                previous = item.get("previous_filename")
                if status == "renamed":
                    if not safe_path(previous) or previous == path:
                        raise ValueError("invalid rename source path")
                    touched.append(previous)
                elif previous is not None:
                    raise ValueError("unexpected rename source path")
                changed.append(path)
                touched.append(path)
        if len(changed) != before or len(set(changed)) != before:
            raise ValueError("PR change count or duplicate mismatch")
        if len(touched) != len(set(touched)):
            raise ValueError("duplicate or ambiguous rename endpoints")
        if set(touched) != set(plan["planned_paths"]):
            raise ValueError("PR diff scope mismatch")
        # A forbidden path names that path AND its directory descendants.
        # The slash boundary avoids rejecting unrelated siblings (v2/app2).
        forbidden = [scope.rstrip("/") for scope in plan["forbidden_scope"]]
        if any(path == scope or path.startswith(scope + "/")
               for path in touched for scope in forbidden):
            raise ValueError("PR forbidden scope")
        after = get_pr()
        if after != before:
            raise ValueError("PR files changed during audit")
        return []
    except (OSError, urllib.error.URLError, ValueError, TypeError,
            KeyError, AttributeError, OverflowError) as exc:
        return ["PR diff evidence rejected: " + str(exc)]



def inspect_live_provenance_candidate(d, trusted, token, fetch):
    """Read-only bridge diagnostic, NEVER an independent approval or PASS.

    Check the *live* GitHub comment/plan and the PR file scope using existing
    readers, then re-read the comment after the PR audit. Caller-supplied
    anchors, issuer flags, cancellation flags, and transport results are NOT
    independent authority. A separately provisioned protected issuer, fresh
    revocation decision, and merge-time binding remain mandatory and absent.
    """
    blocked = ("PROVENANCE_BLOCKED: independent issuer authentication, "
               "fresh revocation authority and mandatory check are not provisioned")
    if (not isinstance(d, dict) or not isinstance(trusted, dict) or
            not isinstance(token, str) or not token or not callable(fetch) or
            trusted.get("repository") != "kan1975-creator/CB6-Navi-Public-Build"):
        return ["invalid live provenance inputs", blocked]
    try:
        # The scope must refer to the SAME digest as the plan fetched from
        # GitHub by _verify_with_transport; no separately caller-picked scope.
        if (plan_digest(trusted["plan"]) != trusted["plan_sha256"] or
                not DIGEST.fullmatch(trusted["plan_sha256"])):
            raise ValueError("candidate scope plan hash mismatch")
        errors = _verify_with_transport(d, trusted, token, fetch)
        if errors:
            return errors + [blocked]
        errors = verify_pr_diff_with_transport(d, trusted, token, fetch)
        if errors:
            return errors + [blocked]
        # A removed/edited approval during the PR audit must be rejected.
        # This is NOT a proof of absence of a separate revocation event.
        comment_id = trusted["comment_id"]
        if type(comment_id) is not int or comment_id <= 0:
            raise ValueError("invalid approval comment id")
        comment = fetch(trusted["repository"],
                        "/issues/comments/" + str(comment_id), token)
        errors = check(d, comment, trusted)
        if errors:
            return errors + [blocked]
    except (OSError, urllib.error.URLError, KeyError, ValueError,
            TypeError, AttributeError, OverflowError) as exc:
        return ["live provenance candidate rejected: " + str(exc), blocked]
    # Success here means only that read-only checks found no contradiction.
    # NO state or environment value is allowed to turn this into PASS.
    return [blocked]


def observe_independent_check_candidate(d, token, fetch=github_get, issuer_app_id=None):
    """Read-only C-05/C-07 check bridge; NEVER grants approval or a PASS.

    GitHub REST is authenticated using the gate's credential. The App ID must
    come from a separately provisioned trusted configuration, not PR content.
    A Check name, stale Check or approval comment alone has no authority to
    prove pre-implementation approval and COMPLETE non-revocation.
    """
    blocked = "PROVENANCE_BLOCKED: issuer's protected approval/start/revocation authority unproven"
    try:
        if not isinstance(d, dict) or not isinstance(token, str) or not token:
            raise ValueError("missing independent issuer transport")
        if type(issuer_app_id) is not int or issuer_app_id <= 0:
            raise ValueError("independent issuer App ID unprovisioned")
        repo = d["repository"]
        head = d["pr_head_sha"]
        change = d["proposed_change_id"]
        plan_hash = d["plan_sha256"]
        if not isinstance(plan_hash, str) or not DIGEST.fullmatch(plan_hash):
            raise ValueError("issuer plan SHA-256 binding invalid")
        if repo != "kan1975-creator/CB6-Navi-Public-Build" or not SHA.fullmatch(head):
            raise ValueError("independent issuer repository or HEAD mismatch")
        if not isinstance(change, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", change):
            raise ValueError("independent issuer change binding invalid")
        # GitHub Check API is scoped to an immutable head; paginate conservatively
        # and reject partial results to avoid treating missing evidence as consent.
        data = fetch(repo, "/commits/" + head + "/check-runs?per_page=100", token)
        if not isinstance(data, dict) or type(data.get("total_count")) is not int or not (0 <= data["total_count"] <= 100):
            raise ValueError("incomplete issuer check results")
        runs = data.get("check_runs")
        if not isinstance(runs, list) or len(runs) != data["total_count"]:
            raise ValueError("incomplete issuer check page")
        seen = []
        for item in runs:
            if not isinstance(item, dict) or item.get("name") != "CB6 Approval Enforcement":
                continue
            if item.get("head_sha") != head:
                raise ValueError("issuer check HEAD mismatch")
            expected_external_id = "CB6-BLOCKED:" + change + ":" + plan_hash + ":" + head
            if item.get("external_id") != expected_external_id:
                raise ValueError("issuer check change/plan/HEAD binding mismatch")
            app = item.get("app")
            if not isinstance(app, dict) or app.get("id") != issuer_app_id:
                raise ValueError("issuer App identity mismatch")
            # The fixed request name alone is not authorization; note outcome
            # without trusting any positive result as evidence of cancellation.
            if item.get("status") != "completed" or item.get("conclusion") != "failure":
                raise ValueError("issuer check does not prove protected consent")
            seen.append(item)
        if not seen:
            raise ValueError("no authenticated blocking issuer Check")
        return [blocked]
    except (OSError, urllib.error.URLError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return ["independent issuer observation rejected: " + str(exc), blocked]



def inspect_live_blocked_issuer_candidate(d, token, fetch=github_get,
                                          issuer_app_id=None, issuer_repo_id=None):
    """Read-only negative-only issuer handshake; never production authorization.

    C-05 re-reads the *live* PR before and after the Check observation, using
    separately provisioned immutable GitHub App/repository identities. A failure
    Check for an obsolete HEAD or another plan/App is not trusted. This is a
    diagnostic only; missing independent custody always blocks success.
    """
    blocked = "PROVENANCE_BLOCKED: independent protected consent and revocation authority not established"
    try:
        if not isinstance(d, dict) or not isinstance(token, str) or not token:
            raise ValueError("independent issuer transport missing")
        if type(issuer_app_id) is not int or issuer_app_id <= 0:
            raise ValueError("issuer App ID not independently configured")
        if type(issuer_repo_id) is not int or issuer_repo_id <= 0:
            raise ValueError("issuer repository ID not independently configured")
        repo = d["repository"]
        if repo != "kan1975-creator/CB6-Navi-Public-Build":
            raise ValueError("issuer repository mismatch")
        number = d["pr_number"]
        head = d["pr_head_sha"]
        base = d["pr_base_sha"]
        base_ref = d["pr_base_ref"]
        if type(number) is not int or number <= 0 or not SHA.fullmatch(head) or                 not SHA.fullmatch(base) or base_ref not in ("main", "cb6-v2-clean"):
            raise ValueError("issuer PR/base/HEAD binding invalid")
        def live_pr():
            pr = fetch(repo, "/pulls/" + str(number), token)
            if not isinstance(pr, dict) or pr.get("number") != number or pr.get("state") != "open":
                raise ValueError("issuer PR unavailable")
            prbase = pr.get("base")
            prhead = pr.get("head")
            if not isinstance(prbase, dict) or not isinstance(prhead, dict) or                     prbase.get("sha") != base or prbase.get("ref") != base_ref or                     not isinstance(prbase.get("repo"), dict) or                     prbase["repo"].get("id") != issuer_repo_id or                     prbase["repo"].get("full_name") != repo or                     prhead.get("sha") != head:
                raise ValueError("issuer live PR/HEAD mismatch")
        live_pr()
        observed = observe_independent_check_candidate(d, token, fetch, issuer_app_id)
        if len(observed) != 1 or observed[0] != (
                "PROVENANCE_BLOCKED: issuer's protected approval/start/revocation authority unproven"):
            return ["issuer Check binding rejected: " + "; ".join(observed), blocked]
        live_pr()
        return [blocked]
    except (OSError, urllib.error.URLError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return ["issuer live handshake rejected: " + str(exc), blocked]


def inspect_captured_timeline_candidate(identity, start_rows, decision_rows):
    """Negative-only C-05/C-07 diagnostic; NEVER an authorization verdict.

    Rows from D1 are not protected custody and could be incomplete or
    modified by its administrator. Even a fully consistent chronology remains
    blocked until independent provenance, revocation and live HEAD are proven.
    """
    blocked = "PROVENANCE_BLOCKED: captured timeline has no protected start/revocation authority"
    errors = []
    try:
        if not isinstance(identity, dict) or not isinstance(start_rows, list) or not isinstance(decision_rows, list):
            raise ValueError("invalid timeline inputs")
        keys = ("repository_id", "pr_number", "change_id", "plan_sha256", "plan_commit_sha", "basis_head")
        if type(identity.get("repository_id")) is not int or identity["repository_id"] <= 0:
            raise ValueError("invalid repository ID")
        if type(identity.get("pr_number")) is not int or identity["pr_number"] <= 0:
            raise ValueError("invalid PR number")
        if (not isinstance(identity.get("change_id"), str) or
                not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", identity["change_id"])):
            raise ValueError("invalid change binding")
        if (not isinstance(identity.get("plan_sha256"), str) or
                not DIGEST.fullmatch(identity["plan_sha256"]) or
                not isinstance(identity.get("plan_commit_sha"), str) or
                not SHA.fullmatch(identity["plan_commit_sha"])):
            raise ValueError("invalid plan binding")
        if not isinstance(identity.get("head_sha"), str) or not SHA.fullmatch(identity["head_sha"]):
            raise ValueError("invalid HEAD binding")
        if not isinstance(identity.get("basis_head"), str) or not SHA.fullmatch(identity["basis_head"]):
            raise ValueError("invalid basis HEAD binding")
        for row in start_rows + decision_rows:
            if not isinstance(row, dict) or any(row.get(k) != identity[k] for k in keys):
                raise ValueError("cross-plan event mismatch")
            if row.get("pr_head_sha") != identity["head_sha"]:
                raise ValueError("stale PR HEAD observation")
            instant(row["github_created_at"])
        if len(start_rows) != 1:
            errors.append("missing or ambiguous captured start")
        approvals = [r for r in decision_rows if r.get("decision") == "APPROVE"]
        revokes = [r for r in decision_rows if r.get("decision") == "REVOKE"]
        if any(r.get("decision") not in ("APPROVE", "REVOKE") for r in decision_rows):
            errors.append("invalid decision event")
        if len(approvals) != 1:
            errors.append("missing or ambiguous captured approval")
        if revokes:
            errors.append("recorded revocation blocks approval")
        if start_rows and approvals and instant(approvals[0]["github_created_at"]) >= instant(start_rows[0]["github_created_at"]):
            errors.append("approval not before captured start")
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError) as exc:
        errors.append("captured timeline rejected: " + str(exc))
    return errors + [blocked]


def verify_live(d, trusted, token):
    """Production entrypoint: UNCONDITIONAL fail-close until anchor is implemented.

    Caller booleans, environment variables, mock transports, or PR code cannot
    provision a protected trust root. The stage-2 candidate deliberately has
    no authority to return success. Future activation needs separate approval,
    protected workflow provenance and genuine end-to-end evidence.
    """
    return ["PROVENANCE_BLOCKED: independently protected trust anchor, "
            "implementation-start control and mandatory check are unprovisioned"]


def verify_legacy_structure(d):
    """Legacy syntax only: never grants authenticated approval."""
    if not isinstance(d, dict):
        return ["invalid evidence"]
    a = d.get("approval")
    if not isinstance(a, dict):
        return ["missing approval"]
    errors = ["legacy evidence is not authenticated approval"]
    for k in CONTRACT["approval_record"]["required_fields"]:
        if not a.get(k):
            errors.append("missing approval field: " + k)
    if a.get("proposed_change_id") != d.get("proposed_change_id"):
        errors.append("approval binding mismatch")
    if not a.get("github_reference"):
        errors.append("missing github approval reference")
    try:
        if instant(a["approved_at"]) >= instant(d["implementation_started_at"]):
            errors.append("approval is not pre-implementation")
    except (KeyError, TypeError, ValueError, AttributeError):
        errors.append("invalid legacy timestamp")
    return errors

def main(argv):
    if len(argv) != 3:
        print("usage: verify_user_approval_before_fix.py evidence.json trusted-config.json")
        return 1
    try:
        evidence = json.loads(Path(argv[1]).read_text())
        trusted = json.loads(Path(argv[2]).read_text())
        if not isinstance(trusted, dict) or not trusted.get("trust_anchor_provisioned_externally"):
            raise ValueError("external trust anchor not established")
        if not trusted.get("implementation_event_verified") or not trusted.get("plan_anchor_verified"):
            raise ValueError("external provenance not verified")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN missing")
        errors = verify_live(evidence, trusted, token)
    except (OSError, ValueError, TypeError) as exc:
        errors = ["configuration failure: " + str(exc)]
    if errors:
        print("CB6 PRE-FIX USER APPROVAL FAIL:", *errors, sep="\n - ")
        return 1
    print("CB6 PRE-FIX USER APPROVAL PASS: authenticated production enforcement")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
