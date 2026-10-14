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
# Legacy PR #7 has stage1, while the separately reviewed personal JSON is schema-1.
# The personal checker does not rely on caller-supplied trust booleans or stage1.
FIELDS = CONTRACT.get("stage1", {}).get("canonical_plan_fields", (
    "proposed_change_id", "basis_head", "planned_paths", "forbidden_scope", "affected_domains"))
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
    # Schema-1 personal contract deliberately lacks the legacy stage1 section.
    # Do not raise KeyError or fabricate a user ID for legacy callers.
    stage1 = CONTRACT.get("stage1")
    if (not isinstance(stage1, dict) or
            type(stage1.get("trusted_github_user_id")) is not int or
            stage1["trusted_github_user_id"] <= 0):
        return errors + ["legacy stage1 trust configuration missing"]
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
        if github_comment["user"]["id"] != stage1["trusted_github_user_id"]:
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



# PERSONAL_APPROVAL_V1 — isolated, reduced-assurance, read-only/manual candidate.
#!/usr/bin/env python3
"""CB6 personal-use read-only approval inspection candidate.

Reduced assurance: GitHub server records can establish approval predates PR
creation, NOT first local edit. This cannot enforce merging or bypass protection.
No writes, no secrets other than ephemeral read-only GITHUB_TOKEN.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

PERSONAL_REPO = 'kan1975-creator/CB6-Navi-Public-Build'
PERSONAL_REPO_ID = 1381480671
PERSONAL_HEX40 = re.compile(r'^[a-f0-9]{40}$')
PERSONAL_HEX64 = re.compile(r'^[a-f0-9]{64}$')
PERSONAL_CHANGE_ID = re.compile(r'^[A-Za-z0-9_.-]{1,128}$')
PERSONAL_MAX_FILES = 3000  # GitHub REST pull-requests/files documented cap

class PersonalBlocked(Exception):
    pass

def personal_require(condition, reason):
    if not condition:
        raise PersonalBlocked(reason)

def personal_utc(value):
    personal_require(isinstance(value, str), 'invalid GitHub timestamp')
    try:
        d = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise PersonalBlocked('invalid GitHub timestamp') from exc
    personal_require(d.tzinfo is not None, 'naive GitHub timestamp')
    return d.astimezone(dt.timezone.utc)

def personal_digest_plan(plan):
    personal_require(isinstance(plan, dict), 'plan must be an object')
    keys = ('proposed_change_id', 'basis_head', 'planned_paths', 'forbidden_scope', 'affected_domains')
    personal_require(all(k in plan for k in keys), 'plan missing legacy digest field')
    normalized = {k: plan[k] for k in keys}
    for k in ('planned_paths', 'forbidden_scope', 'affected_domains'):
        personal_require(isinstance(normalized[k], list) and all(isinstance(x, str) for x in normalized[k]), 'plan array invalid')
        normalized[k] = sorted(normalized[k])
    wire = json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(wire).hexdigest()

def personal_validate_plan(plan):
    personal_require(isinstance(plan.get('proposed_change_id'), str) and PERSONAL_CHANGE_ID.fullmatch(plan['proposed_change_id']), 'bad change ID')
    personal_require(isinstance(plan.get('basis_head'), str) and PERSONAL_HEX40.fullmatch(plan['basis_head']), 'bad basis HEAD')
    planned = plan.get('planned_paths')
    forbidden = plan.get('forbidden_scope')
    personal_require(isinstance(planned, list) and 0 < len(planned) <= PERSONAL_MAX_FILES, 'planned paths missing/out of bounds')
    for arr in (planned, forbidden):
        personal_require(isinstance(arr, list), 'scope must be array')
        for path in arr:
            personal_require(isinstance(path, str) and 0 < len(path) <= 250 and not path.startswith('/')
                    and all(seg not in ('', '.', '..') for seg in path.split('/')),
                    'unsafe scope path')
    personal_require(len(set(planned)) == len(planned), 'duplicate planned paths')
    personal_require(not set(planned).intersection(forbidden), 'forbidden path in plan')

def personal_gh_get(path, token, transport=None):
    if transport is not None:
        return transport(path)
    request = urllib.request.Request(
        'https://api.github.com/repos/' + PERSONAL_REPO + path,
        headers={'Accept': 'application/vnd.github+json',
                 'Authorization': 'Bearer ' + token,
                 'X-GitHub-Api-Version': '2022-11-28',
                 'User-Agent': 'CB6-personal-approval-readonly'})
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            return json.load(resp)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise PersonalBlocked('GitHub API unavailable or malformed') from exc

def personal_scope_files(api, number, count):
    personal_require(type(count) is int and 0 < count <= PERSONAL_MAX_FILES, 'PR file count invalid or exceeds GitHub limit')
    rows=[]
    for page in range(1, (count + 99)//100+1):
        part = api(f'/pulls/{number}/files?per_page=100&page={page}')
        personal_require(isinstance(part, list) and len(part) > 0, 'incomplete PR file pagination')
        rows.extend(part)
    personal_require(len(rows) == count, 'PR changed-file count mismatch')
    names=[]
    for row in rows:
        personal_require(isinstance(row, dict) and isinstance(row.get('filename'), str), 'bad PR file')
        personal_require(row.get('status') in ('added','modified','removed','renamed','copied','changed'), 'unknown PR file status')
        names.append(row['filename'])
        if row.get('status') == 'renamed':
            personal_require(isinstance(row.get('previous_filename'), str), 'missing previous filename')
            names.append(row['previous_filename'])
    personal_require(len(set(names)) == len(names), 'duplicate paths in PR changes')
    return set(names)

def personal_pr_approval_record(pr, comment, change_id, summary):
    """Check the legacy contract's required fields using a PR-description ref.

    The Issue comment is the author-origin approval evidence; its ID, server
    time and human-authored summary MUST be bound into the PR description.
    The comment alone is NOT an additional allowed reference location.
    """
    policy = CONTRACT.get('approval_record')
    personal_require(isinstance(policy, dict) and
            policy.get('github_reference_required') is True and
            policy.get('change_binding') == 'exact_proposed_change_id' and
            'pull_request_description' in policy.get('allowed_reference_locations', []),
            'legacy approval reference policy missing')
    mandatory = {'approval_id','approved_at','proposed_change_id','approved_change_summary'}
    fields = policy.get('required_fields')
    personal_require(isinstance(fields, list) and mandatory.issubset(set(fields)),
            'legacy required approval fields missing')
    personal_require(isinstance(pr.get('body'), str), 'PR description missing')
    source_lines = pr['body'].splitlines()
    def pr_field(tag):
        candidates = [row[len(tag)+1:] for row in source_lines if row.startswith(tag+' ')]
        personal_require(len(candidates) == 1 and bool(candidates[0].strip()),
                'missing or ambiguous PR approval field: ' + tag)
        return candidates[0]
    record = {
        'approval_id': pr_field('CB6-APPROVAL-REF'),
        'approved_at': pr_field('CB6-APPROVED-AT'),
        'proposed_change_id': pr_field('CB6-PROPOSED-CHANGE'),
        'approved_change_summary': pr_field('CB6-APPROVED-SUMMARY'),
    }
    expected = {
        'approval_id': 'issue-comment:'+str(comment['id']),
        'approved_at': comment['created_at'],
        'proposed_change_id': change_id,
        'approved_change_summary': summary,
    }
    for field in fields:
        personal_require(record.get(field) == expected.get(field) and bool(record.get(field)),
                'legacy approval field mismatch: ' + field)
    return record


def personal_repository_comment_snapshot(api, owner_id, change_id, approval):
    """Enumerate repository-wide Issue/PR conversation comments, fail closed.

    GitHub's repository /issues/comments lists comments from all Issues/PRs.
    A short page (including a trailing empty page after a full page) is needed
    to prove pagination was exhausted within the bounded, read-only scan.
    Deleted comments or changes after the final scan cannot be reconstructed.
    """
    rows = []
    for page in range(1, 51):  # explicit bound: <= 5,000 rows
        batch = api(f'/issues/comments?per_page=100&page={page}')
        personal_require(isinstance(batch, list) and len(batch) <= 100 and
                (bool(batch) or page > 1), 'repository-wide comment pagination incomplete')
        rows.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise PersonalBlocked('repository-wide comment scan exceeds bounded pages')
    personal_require(bool(rows), 'no repository-wide comments')
    ids = set()
    snapshot = []
    approvals = 0
    for item in rows:
        personal_require(isinstance(item, dict) and type(item.get('id')) is int and
                item['id'] > 0 and isinstance(item.get('body'), str) and
                isinstance(item.get('user'), dict) and type(item['user'].get('id')) is int and
                isinstance(item.get('created_at'), str) and
                isinstance(item.get('updated_at'), str) and
                isinstance(item.get('issue_url'), str) and
                re.fullmatch(r'https://api\.github\.com/repos/'+re.escape(PERSONAL_REPO)+
                             r'/issues/[1-9][0-9]*', item['issue_url']),
                'malformed repository-wide comment')
        personal_require(item['id'] not in ids, 'duplicate repository-wide comment ID')
        ids.add(item['id'])
        fingerprint = (item['id'],item['body'],item['user']['id'],
                       item['created_at'],item['updated_at'],item['issue_url'])
        snapshot.append(fingerprint)
        if item['id'] == approval['id']:
            # Single-comment and list APIs can return different optional keys.
            # Compare the identity, provenance and text fields, not the whole dict.
            personal_require(fingerprint == (
                approval['id'], approval['body'], approval['user']['id'],
                approval['created_at'], approval['updated_at'], approval['issue_url']),
                'approval changed in repository-wide scan')
            approvals += 1
        if item['user']['id'] == owner_id:
            text = item['body'].strip()
            revoke = 'CB6-REVOKE ' + change_id
            personal_require(not (text == revoke or
                    (text.startswith(revoke) and len(text) > len(revoke) and
                     text[len(revoke)].isspace())),
                    'matching owner revocation found in repository')
    personal_require(approvals == 1, 'approval missing or ambiguous in repository-wide scan')
    return tuple(snapshot)


def personal_check(pr_number, comment_id, plan_sha, plan_commit, plan_path, expected_head, token, transport=None, expected_base_ref=None, expected_base_sha=None):
    personal_require(type(pr_number) is int and pr_number > 0 and type(comment_id) is int and comment_id > 0, 'bad PR/comment ID')
    personal_require(isinstance(plan_sha, str) and PERSONAL_HEX64.fullmatch(plan_sha), 'bad plan SHA256')
    personal_require(isinstance(plan_commit, str) and PERSONAL_HEX40.fullmatch(plan_commit), 'bad plan commit SHA')
    personal_require(isinstance(expected_head, str) and PERSONAL_HEX40.fullmatch(expected_head), 'bad expected PR HEAD')
    personal_require(isinstance(plan_path, str) and 0 < len(plan_path) <= 200 and all(
            seg not in ('', '.', '..') for seg in plan_path.split('/')) and not plan_path.startswith('/'), 'bad plan path')
    personal_require(isinstance(token, str) and token, 'GITHUB_TOKEN missing')
    if expected_base_ref is not None or expected_base_sha is not None:
        personal_require(expected_base_ref in ('main', 'cb6-v2-clean') and
                         isinstance(expected_base_sha, str) and
                         PERSONAL_HEX40.fullmatch(expected_base_sha) is not None,
                         'malformed expected PR base identity')
    api = lambda suffix: personal_gh_get(suffix, token, transport)

    repository = api('')
    personal_require(isinstance(repository, dict) and repository.get('id') == PERSONAL_REPO_ID and
            repository.get('full_name') == PERSONAL_REPO and
            repository.get('owner', {}).get('login') == 'kan1975-creator', 'unexpected repository identity')
    owner_id = repository['owner'].get('id')
    personal_require(type(owner_id) is int and owner_id > 0, 'GitHub owner ID missing')
    pr = api(f'/pulls/{pr_number}')
    personal_require(isinstance(pr, dict) and pr.get('number') == pr_number and pr.get('state') == 'open' and pr.get('draft') is False, 'PR unavailable, closed, or draft')
    personal_require(pr.get('head', {}).get('sha') == expected_head, 'stale PR HEAD')
    personal_require(pr.get('base', {}).get('repo', {}).get('full_name') == PERSONAL_REPO, 'PR base repository mismatch')
    personal_require(pr.get('base', {}).get('ref') in ('main', 'cb6-v2-clean'), 'unsupported base branch')
    if expected_base_ref is not None:
        personal_require(pr['base'].get('ref') == expected_base_ref and
                         pr['base'].get('sha') == expected_base_sha,
                         'authenticated PR base ref/SHA differs from event')
    comment = api(f'/issues/comments/{comment_id}')
    personal_require(isinstance(comment, dict) and comment.get('id') == comment_id and
            comment.get('user', {}).get('id') == owner_id, 'not owner-authored GitHub comment')
    personal_require(comment.get('created_at') == comment.get('updated_at'), 'edited approval comment')
    personal_require(personal_utc(comment['created_at']) < personal_utc(pr['created_at']), 'approval not before PR creation')
    personal_require(isinstance(comment.get('issue_url'), str) and comment['issue_url'].startswith(
        'https://api.github.com/repos/' + PERSONAL_REPO + '/issues/'), 'approval from another repo')
    issue_number_str = comment['issue_url'].split('/')[-1]
    personal_require(issue_number_str.isdigit(), 'invalid approval issue')
    issue_number = int(issue_number_str)

    endpoint = '/contents/' + urllib.parse.quote(plan_path, safe='/') + '?ref=' + plan_commit
    blob = api(endpoint)
    personal_require(isinstance(blob, dict) and blob.get('type') == 'file' and blob.get('encoding') == 'base64', 'missing canonical plan')
    try:
        source = base64.b64decode(blob['content'].replace('\n',''), validate=True)
        plan = json.loads(source.decode('utf-8'))
    except (ValueError, UnicodeError, KeyError, __import__("binascii").Error) as exc:
        raise PersonalBlocked('malformed canonical plan') from exc
    personal_validate_plan(plan)
    personal_require(personal_digest_plan(plan) == plan_sha, 'plan SHA mismatch')
    personal_require(plan['basis_head'] == pr['base']['sha'], 'plan vs PR base mismatch')
    expected_body = f"CB6-APPROVE {plan['proposed_change_id']} {plan_sha} {plan_commit}"
    personal_require(isinstance(comment.get('body'), str), 'approval text missing')
    approval_lines = comment['body'].splitlines()
    personal_require(len(approval_lines) == 2 and approval_lines[0] == expected_body,
            'approval text/change binding mismatch')
    prefix = 'CB6-APPROVED-SUMMARY '
    personal_require(approval_lines[1].startswith(prefix), 'approved summary missing from comment')
    summary = approval_lines[1][len(prefix):]
    personal_require(bool(summary.strip()) and summary == summary.strip() and
            len(summary) <= 200 and not any(ord(c) < 32 for c in summary),
            'invalid approved summary')
    personal_pr_approval_record(pr, comment, plan['proposed_change_id'], summary)

    seen = personal_scope_files(api, pr_number, pr.get('changed_files'))
    personal_require(seen == set(plan['planned_paths']), 'changed files do not match approved scope')
    personal_require(not seen.intersection(plan['forbidden_scope']), 'forbidden change path')
    issue = api(f'/issues/{issue_number}')
    count = issue.get('comments') if isinstance(issue, dict) else None
    personal_require(type(count) is int and 1 <= count <= 500, 'approval issue count outside inspectable bound')
    matching_approvals = 0
    all_comments=[]
    for page in range(1,(count+99)//100+1):
        batch = api(f'/issues/{issue_number}/comments?per_page=100&page={page}')
        personal_require(isinstance(batch, list) and batch, 'incomplete approval issue pagination')
        all_comments.extend(batch)
    personal_require(len(all_comments) == count and len({c.get('id') for c in all_comments if isinstance(c,dict)}) == count,
            'approval issue pagination mismatch')
    for item in all_comments:
        personal_require(isinstance(item,dict) and isinstance(item.get('body'), str), 'malformed issue comment')
        if item.get('id') == comment_id:
            personal_require(item['body'] == comment['body'] and item.get('updated_at') == comment['updated_at'],
                    'approval changed during scan')
            matching_approvals += 1
        if item.get('user',{}).get('id') == owner_id:
            rev = 'CB6-REVOKE ' + plan['proposed_change_id']
            body=item['body'].strip()
            personal_require(body != rev and not body.startswith(rev+' '), 'matching user revocation exists')
    personal_require(matching_approvals == 1, 'approval not found in issue')
    # The home Issue is not the entire revocation domain. Read *all* repository
    # Issue comments, including those posted under a different Issue or PR.
    repository_snapshot = personal_repository_comment_snapshot(
            api, owner_id, plan['proposed_change_id'], comment)
    latest_pr=api(f'/pulls/{pr_number}')
    latest_comment=api(f'/issues/comments/{comment_id}')
    if expected_base_ref is not None:
        personal_require(latest_pr.get('base', {}).get('ref') == expected_base_ref and
                         latest_pr.get('base', {}).get('sha') == expected_base_sha and
                         latest_pr.get('base', {}).get('repo', {}).get('full_name') == PERSONAL_REPO,
                         'authenticated PR base identity changed during verification')
    personal_require(latest_pr.get('head', {}).get('sha') == expected_head and
            latest_pr.get('base', {}).get('sha') == pr['base']['sha'] and
            latest_pr.get('changed_files') == pr['changed_files'] and
            latest_pr.get('created_at') == pr['created_at'] and
            latest_pr.get('body') == pr['body'] and
            latest_pr.get('state') == 'open' and latest_pr.get('draft') is False, 'PR changed during verification')
    personal_require(latest_comment == comment, 'approval changed during verification')
    personal_require(api(f'/issues/{issue_number}').get('comments') == count, 'comment count changed during verification')
    personal_require(personal_repository_comment_snapshot(
            api, owner_id, plan['proposed_change_id'], comment) == repository_snapshot,
            'repository comments changed between scans')
    return 'PERSONAL_APPROVAL_V1_PR_PROXY_ONLY'

# USER-APPROVED 2026-10-13 POLICY, PROPOSED / NOT DEPLOYED.
# This guard cannot authorize a Required Check or change legacy verify_live().
def personal_completion_policy_guard(document=None):
    document = CONTRACT if document is None else document
    personal_require(isinstance(document, dict) and
                     document.get('status') == 'CANDIDATE',
                     'personal completion policy cannot activate the contract')
    record = document.get('personal_completion_policy_20261013')
    expected = {'status': 'USER_APPROVED_POLICY_ONLY', 'authorization': 'ISOLATED_LOCAL_CANDIDATE_ONLY', 'record_date': '2026-10-13', 'scope': 'PERSONAL_DEVELOPMENT_ONLY', 'administrator_self_lock_guarantee': 'UNATTAINABLE_NOT_REQUIRED', 'administrator_settings_changes': 'AUDIT_WITH_EXPLICIT_OWNER_DECISION_NOT_PREVENTION', 'historical_unrecorded_local_edit': 'UNPROVEN_NEVER_RETROACTIVE_PASS', 'future_preimplementation_owner_approval': 'REQUIRED_CHANGE_BOUND_BEFORE_WORK', 'future_evidence': 'FIXED_PLAN_SHA_APPROVAL_RECORD_AND_START_LOG_WITHOUT_ABSOLUTE_LOCAL_TIME_PROOF', 'external_independent_issuer': 'NOT_REQUIRED_FOR_PERSONAL_COMPLETION_POLICY', 'external_human_administrator': 'NOT_REQUIRED_FOR_PERSONAL_COMPLETION_POLICY', 'separate_gpt_independent_review': 'REQUIRED', 'affected_scope_tests': 'REQUIRED', 'legacy_verify_live': 'RETAIN_UNCONDITIONAL_PROVENANCE_BLOCKED', 'github_required_check': 'REQUIRED_FOR_FINAL_COMPLETION_NOT_IMPLEMENTED', 'workflow_trigger_selection': 'UNSELECTED_PENDING_SECURITY_VALIDATION', 'untrusted_pr_code_at_privileged_scope': 'FORBIDDEN', 'active_registry_v21': 'UNCHANGED', 'registry_v22': 'PROPOSED_NOT_ACTIVE', 'write_and_method_freezes': 'UNCHANGED', 'final_owner_adoption': 'SEPARATELY_REQUIRED_AFTER_EVIDENCE', 'production_deployment': 'NOT_AUTHORIZED'}
    personal_require(isinstance(record, dict) and
                     record == expected,
                     'personal completion policy proposal changed or activated')
    personal_require(document.get('personal_issuer_relaxation_candidate', {}).get('status') ==
                     'PROPOSED_NOT_ADOPTED' and
                     document.get('personal_formal_transition_proposal', {}).get('allow_production_pass') is False,
                     'personal completion policy cannot authorize production')
    return 'USER_APPROVED_POLICY_ONLY_NOT_DEPLOYED'


def personal_transition_proposal_guard(policy=None):
    """Read-only proposal guard; NEVER grants production/Required Check authority."""
    policy = CONTRACT if policy is None else policy
    personal_require(isinstance(policy, dict) and policy.get('status') == 'CANDIDATE',
                     'personal transition is not an active contract')
    personal = policy.get('personal_issuer_relaxation_candidate', {})
    decision = personal.get('user_completion_criteria_decision', {})
    candidate = policy.get('personal_formal_transition_proposal', {})
    personal_require(personal.get('status') == 'PROPOSED_NOT_ADOPTED' and
                     personal.get('does_not_override_active_rules') is True and
                     decision.get('status') == 'USER_APPROVED_POLICY_ONLY' and
                     decision.get('deployment_status') == 'NOT_DEPLOYED' and
                     decision.get('active_rules_unchanged') is True,
                     'personal policy adoption/provenance invalid')
    personal_require(candidate.get('status') == 'PROPOSED_NOT_ACTIVE' and
                     candidate.get('method') == 'PERSONAL_MANUAL_READ_ONLY_ADVISORY' and
                     candidate.get('allow_production_pass') is False and
                     candidate.get('active_rules_unchanged') is True and
                     candidate.get('deployment_status') == 'NOT_DEPLOYED',
                     'personal transition guard is missing or activated')
    personal_completion_policy_guard(policy)
    prereqs = candidate.get('requires_before_deployment')
    personal_require(isinstance(prereqs, list) and
                     all(isinstance(v, str) for v in prereqs) and
                     {'explicit_user_final_adoption','separate_gpt_independent_review',
                      'trusted_main_execution','read_only_github_api_token',
                      'affected_scope_change_tests',
                      'required_active_registry_migration_and_freeze_compliance'}.issubset(set(prereqs)),
                     'transition prerequisites missing')
    return 'PERSONAL_TRANSITION_PROPOSED_UNDEPLOYED'



# PROPOSED AUTO CANDIDATE ONLY. Not a production check and not ACTIVE authority.
# Only the PR's *metadata* is parsed. The authenticated personal_check() fetches
# GitHub API records afresh and rejects mismatch, change, revocation or API loss.
PERSONAL_AUTO_ACTIONS = frozenset({
    'opened', 'reopened', 'synchronize', 'edited', 'ready_for_review'
})

def personal_pr_event_inputs(event, repository, event_name):
    """Convert untrusted webhook DATA to strictly validated personal_check args."""
    personal_require(event_name == 'pull_request', 'not a pull_request event')
    personal_require(repository == PERSONAL_REPO, 'wrong event repository')
    personal_require(isinstance(event, dict) and event.get('action') in PERSONAL_AUTO_ACTIONS,
                     'unhandled PR event action')
    pr = event.get('pull_request')
    personal_require(isinstance(pr, dict) and pr.get('draft') is False,
                     'draft or missing PR')
    number = event.get('number')
    personal_require(type(number) is int and number > 0 and number == pr.get('number'),
                     'PR event number mismatch')
    base = pr.get('base')
    head = pr.get('head')
    personal_require(isinstance(base, dict) and isinstance(head, dict) and
                     base.get('ref') in ('main', 'cb6-v2-clean') and
                     base.get('repo', {}).get('full_name') == PERSONAL_REPO,
                     'PR event base invalid')
    expected_head = head.get('sha')
    personal_require(isinstance(expected_head, str) and PERSONAL_HEX40.fullmatch(expected_head),
                     'PR event HEAD invalid')
    personal_require(isinstance(pr.get('body'), str), 'PR body unavailable')
    rows = pr['body'].splitlines()
    def field(key):
        matches = [line[len(key)+1:] for line in rows if line.startswith(key+' ')]
        personal_require(len(matches) == 1 and matches[0] and
                         len(matches[0]) <= 250 and matches[0] == matches[0].strip(),
                         'missing or duplicate PR approval metadata: ' + key)
        return matches[0]
    approval_ref = field('CB6-APPROVAL-REF')
    m = re.fullmatch(r'issue-comment:([1-9][0-9]{0,17})', approval_ref)
    personal_require(m is not None, 'bad GitHub approval reference')
    plan_sha = field('CB6-PLAN-SHA256')
    plan_commit = field('CB6-PLAN-COMMIT')
    plan_path = field('CB6-PLAN-PATH')
    personal_require(PERSONAL_HEX64.fullmatch(plan_sha) is not None and
                     PERSONAL_HEX40.fullmatch(plan_commit) is not None and
                     0 < len(plan_path) <= 200 and not plan_path.startswith('/') and
                     all(segment not in ('', '.', '..') for segment in plan_path.split('/')),
                     'invalid PR plan metadata')
    # The timestamp/change/summary fields are still required by personal_check
    # and must match the authenticated approval comment. Never trust PR claims.
    for key in ('CB6-APPROVED-AT', 'CB6-PROPOSED-CHANGE', 'CB6-APPROVED-SUMMARY'):
        field(key)
    return (number, int(m.group(1)), plan_sha, plan_commit, plan_path, expected_head)


def personal_pr_auto_main(environ=None, event=None, checker=None):
    """Candidate-only: fails closed unless API-backed personal_check succeeds.

    This must only be run from a trusted checkout *after* a separately authorized
    rollout. A pull_request workflow sourced from an untrusted PR merge is not
    independently authoritative for Required Check enforcement.
    """
    environ = os.environ if environ is None else environ
    try:
        personal_transition_proposal_guard()
        personal_require(environ.get('GITHUB_EVENT_NAME') == 'pull_request' and
                         environ.get('GITHUB_REPOSITORY') == PERSONAL_REPO,
                         'unexpected GitHub event identity')
        personal_require(environ.get('GITHUB_BASE_REF') in ('main','cb6-v2-clean'),
                         'unexpected PR base ref')
        token = environ.get('GITHUB_TOKEN', '')
        personal_require(isinstance(token, str) and token, 'GITHUB_TOKEN missing')
        if event is None:
            path = environ.get('GITHUB_EVENT_PATH', '')
            personal_require(bool(path) and Path(path).is_file(), 'GitHub event file missing')
            try:
                event = json.loads(Path(path).read_text(encoding='utf-8'))
            except (OSError, ValueError) as exc:
                raise PersonalBlocked('malformed GitHub event payload') from exc
        args = personal_pr_event_inputs(event, environ['GITHUB_REPOSITORY'],
                                        environ['GITHUB_EVENT_NAME'])
        personal_require(event['pull_request']['base']['ref'] ==
                         environ['GITHUB_BASE_REF'], 'environment/event base mismatch')
        func = personal_check if checker is None else checker
        outcome = func(*args, token)
        personal_require(outcome == 'PERSONAL_APPROVAL_V1_PR_PROXY_ONLY',
                         'personal approval result not accepted')
        print('CANDIDATE AUTO PASS: PERSONAL_APPROVAL_V1_PR_PROXY_ONLY')
        print('NOTE: Not production authorization, not an independently protected Required Check.')
        return 0
    except (PersonalBlocked, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print('CANDIDATE AUTO BLOCK:', str(exc), file=sys.stderr)
        return 1

def personal_main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--pr', type=int, required=True)
    p.add_argument('--comment-id', type=int, required=True)
    p.add_argument('--plan-sha', required=True)
    p.add_argument('--plan-commit', required=True)
    p.add_argument('--plan-path', required=True)
    p.add_argument('--expected-head', required=True)
    a=p.parse_args(argv)
    try:
        policy = CONTRACT.get("personal_issuer_relaxation_candidate", {})
        personal_require(
            policy.get("status") == "PROPOSED_NOT_ADOPTED" and
            policy.get("scope") == "PERSONAL_DEVELOPMENT_ONLY" and
            policy.get("does_not_override_active_rules") is True,
            "personal candidate contract missing or invalid")
        personal_transition_proposal_guard()
        status = personal_check(a.pr, a.comment_id, a.plan_sha, a.plan_commit,
                       a.plan_path, a.expected_head, os.environ.get('GITHUB_TOKEN', ''))
        print('CANDIDATE PASS:', status)
        print('NOTE: GitHub approval precedes PR creation, not proven before first local edit.')
        print('NOTE: advisory only; Required Check, write protection and Freeze are unchanged.')
        return 0
    except (PersonalBlocked, KeyError, TypeError, ValueError, AttributeError) as exc:
        print('CANDIDATE BLOCK:', str(exc), file=sys.stderr)
        return 1




# Trusted-default-main PR target adapter, ISOLATED CANDIDATE ONLY.
# This accepts only event metadata; it NEVER checks out, imports or executes PR code.
# The enclosing workflow must run from trusted default main with read-only token.
# GitHub Actions event policy for pull_request_target remains UNVERIFIED;
# this module does not authorize deployment or Required Check registration.
def personal_trusted_target_candidate_main(environ=None, event=None, checker=None):
    environ = os.environ if environ is None else environ
    if CONTRACT.get('status') == 'ACTIVE':
        # Compatibility for the historical CLI entrypoint after formal adoption.
        # Never execute candidate-only checks or print a candidate PASS in ACTIVE.
        # Delegate to the strict active verifier; it fails closed on drift/errors.
        return personal_trusted_target_required_main(environ=environ, event=event,
                                                     checker=checker)
    try:
        personal_transition_proposal_guard()
        # Complete equality rejects missing, extra or weakened auto-contract fields.
        expected_auto = {'status': 'PROPOSED_NOT_ACTIVE',
         'method': 'TRUSTED_DEFAULT_MAIN_PULL_REQUEST_TARGET_METADATA_ONLY',
         'event': 'pull_request_target',
         'allowed_base_branches': ['main', 'cb6-v2-clean'],
         'separately_deploy_trusted_workflow_to_each_base': False,
         'execute_pr_head_or_merge_code': False,
         'github_token_permissions': ['contents:read', 'issues:read', 'pull-requests:read'],
         'skip_success_as_required_check': False,
         'actions_policy_verified': False,
         'required_check_live_verified': False,
         'required_checks': 'NOT_REGISTERED',
         'allow_production_pass': False,
         'active_rules_unchanged': True,
         'deployment_status': 'NOT_DEPLOYED',
         'trusted_workflow_source_branch': 'main',
         'trusted_event_ref': 'refs/heads/main',
         'pr_base_match_sources': ['GITHUB_BASE_REF', 'event.pull_request.base', 'authenticated_github_api_pr'],
         'checkout_trusted_default_branch_sha_only': True,
         'trusted_workflow_sha256': 'e6b2c117a5d7bc93a667522dc3a14b360d995b0e240c4aef0f494b418a2f6bb3'}
        personal_require(CONTRACT.get('personal_trusted_target_auto_candidate') == expected_auto,
                         'trusted-default-main auto contract missing, altered or activated')
        # Bind declared permissions, event trigger and trusted checkout to exact
        # trusted-main workflow bytes; a YAML/contract drift fails closed.
        workflow_path = ROOT / '.github/workflows/cb6_approval_enforcement.yml'
        personal_require(hashlib.sha256(workflow_path.read_bytes()).hexdigest() ==
                         expected_auto['trusted_workflow_sha256'],
                         'trusted-main workflow differs from approved auto contract')
        personal_require(environ.get('GITHUB_EVENT_NAME') == 'pull_request_target',
                         'not a pull_request_target event')
        personal_require(environ.get('GITHUB_REPOSITORY') == PERSONAL_REPO,
                         'unexpected repository identity')
        base_ref = environ.get('GITHUB_BASE_REF')
        personal_require(environ.get('GITHUB_REF') == 'refs/heads/main' and
                         base_ref in expected_auto['allowed_base_branches'],
                         'trusted default-main ref or PR target branch mismatch')
        trusted_sha = environ.get('GITHUB_SHA', '')
        personal_require(isinstance(trusted_sha, str) and
                         PERSONAL_HEX40.fullmatch(trusted_sha) is not None,
                         'trusted base SHA missing or malformed')
        token = environ.get('GITHUB_TOKEN', '')
        personal_require(isinstance(token, str) and bool(token),
                         'read-only GITHUB_TOKEN required')
        if event is None:
            path = environ.get('GITHUB_EVENT_PATH')
            personal_require(isinstance(path, str) and bool(path),
                             'GitHub event path unavailable')
            try:
                event = json.loads(Path(path).read_text(encoding='utf-8'))
            except (OSError, UnicodeError, ValueError) as exc:
                raise PersonalBlocked('unreadable PR target event') from exc
        personal_require(isinstance(event, dict), 'PR target event must be object')
        repository = event.get('repository')
        personal_require(isinstance(repository, dict) and
                         repository.get('full_name') == PERSONAL_REPO,
                         'PR target payload repository mismatch')
        pr = event.get('pull_request')
        personal_require(isinstance(pr, dict), 'PR target payload missing PR')
        base = pr.get('base')
        personal_require(isinstance(base, dict) and base.get('ref') == base_ref and
                         isinstance(base.get('sha'), str) and
                         PERSONAL_HEX40.fullmatch(base['sha']) is not None and
                         base.get('repo', {}).get('full_name') == PERSONAL_REPO,
                         'PR target base identity malformed or mismatched')
        # GITHUB_SHA is the trusted main SHA, not the PR's base SHA.
        # Compare PR base SHA/ref to authenticated API inside personal_check.
        # This parser validates metadata only. Its event_name parameter is a
        # parser label, never a claim that a pull_request workflow was trusted.
        args = personal_pr_event_inputs(event, PERSONAL_REPO, 'pull_request')
        if checker is None:
            outcome = personal_check(*args, token, expected_base_ref=base_ref,
                                     expected_base_sha=base['sha'])
        else:
            # Preserves isolated injected-checker signature; CLI never passes a checker.
            outcome = checker(*args, token)
        personal_require(outcome == 'PERSONAL_APPROVAL_V1_PR_PROXY_ONLY',
                         'authenticated personal approval absent or rejected')
        print('TRUSTED_MAIN_CANDIDATE PASS: GitHub owner PR-approval proxy verified')
        print('NOTE: Candidate result only. No Required Check policy or formal adoption.')
        return 0
    except (PersonalBlocked, OSError, UnicodeError, ValueError, TypeError,
            AttributeError, KeyError) as exc:
        print('TRUSTED_MAIN_CANDIDATE BLOCK:', str(exc), file=sys.stderr)
        return 1



def personal_trusted_target_required_main(environ=None, event=None, checker=None):
    environ = os.environ if environ is None else environ
    try:
        # ACTIVE contract is separate from the immutable historical candidate evidence.
        personal_require(CONTRACT.get('status') == 'ACTIVE', 'active contract not adopted')
        expected_auto = {'status': 'ACTIVE',
         'method': 'TRUSTED_DEFAULT_MAIN_PULL_REQUEST_TARGET_METADATA_ONLY',
         'event': 'pull_request_target',
         'allowed_base_branches': ['main', 'cb6-v2-clean'],
         'separately_deploy_trusted_workflow_to_each_base': False,
         'execute_pr_head_or_merge_code': False,
         'github_token_permissions': ['contents:read', 'issues:read', 'pull-requests:read'],
         'skip_success_as_required_check': False,
         'required_check_context': 'cb6-personal-approval-trusted-candidate',
         'required_check_integration_id': 15368,
         'required_checks': 'GITHUB_BRANCH_RULESET',
         'allow_production_pass': True,
         'require_owner_prior_approval': True,
         'retain_separate_gpt_review': True,
         'retain_affected_scope_tests': True,
         'legacy_verify_live_retains_block': True,
         'assurance_boundary': 'GITHUB_OWNER_APPROVAL_BEFORE_PR_CREATION_AND_APPROVED_PATH_SET_NOT_FIRST_LOCAL_EDIT_OR_CONTENT_HASH',
         'trusted_workflow_source_branch': 'main',
         'trusted_event_ref': 'refs/heads/main',
         'pr_base_match_sources': ['GITHUB_BASE_REF',
                                   'event.pull_request.base',
                                   'authenticated_github_api_pr'],
         'checkout_trusted_default_branch_sha_only': True,
         'trusted_workflow_sha256': 'd79e24ac5e1b79e77e5e71f8ceaf8a03146a6e40ce072881766bf665b925435a',
         'candidate_provenance_run_id': 38571667600,
         'candidate_provenance_main_sha': '401e31b7b03f8c78173ae703f5c8791254dd2cc0',
         'final_adoption_requires': 'OWNER_APPROVAL_AND_EFFECTIVE_RULESET_CHECK_ENFORCEMENT'}
        personal_require(CONTRACT.get('personal_trusted_target_auto_active') == expected_auto,
                         'active required-check contract missing or drifted')
        # Bind declared permissions, event trigger and trusted checkout to exact
        # trusted-main workflow bytes; a YAML/contract drift fails closed.
        workflow_path = ROOT / '.github/workflows/cb6_approval_enforcement.yml'
        personal_require(hashlib.sha256(workflow_path.read_bytes()).hexdigest() ==
                         expected_auto['trusted_workflow_sha256'],
                         'trusted-main workflow differs from approved auto contract')
        personal_require(environ.get('GITHUB_EVENT_NAME') == 'pull_request_target',
                         'not a pull_request_target event')
        personal_require(environ.get('GITHUB_REPOSITORY') == PERSONAL_REPO,
                         'unexpected repository identity')
        base_ref = environ.get('GITHUB_BASE_REF')
        personal_require(environ.get('GITHUB_REF') == 'refs/heads/main' and
                         base_ref in expected_auto['allowed_base_branches'],
                         'trusted default-main ref or PR target branch mismatch')
        trusted_sha = environ.get('GITHUB_SHA', '')
        personal_require(isinstance(trusted_sha, str) and
                         PERSONAL_HEX40.fullmatch(trusted_sha) is not None,
                         'trusted base SHA missing or malformed')
        token = environ.get('GITHUB_TOKEN', '')
        personal_require(isinstance(token, str) and bool(token),
                         'read-only GITHUB_TOKEN required')
        if event is None:
            path = environ.get('GITHUB_EVENT_PATH')
            personal_require(isinstance(path, str) and bool(path),
                             'GitHub event path unavailable')
            try:
                event = json.loads(Path(path).read_text(encoding='utf-8'))
            except (OSError, UnicodeError, ValueError) as exc:
                raise PersonalBlocked('unreadable PR target event') from exc
        personal_require(isinstance(event, dict), 'PR target event must be object')
        repository = event.get('repository')
        personal_require(isinstance(repository, dict) and
                         repository.get('full_name') == PERSONAL_REPO,
                         'PR target payload repository mismatch')
        pr = event.get('pull_request')
        personal_require(isinstance(pr, dict), 'PR target payload missing PR')
        base = pr.get('base')
        personal_require(isinstance(base, dict) and base.get('ref') == base_ref and
                         isinstance(base.get('sha'), str) and
                         PERSONAL_HEX40.fullmatch(base['sha']) is not None and
                         base.get('repo', {}).get('full_name') == PERSONAL_REPO,
                         'PR target base identity malformed or mismatched')
        # GITHUB_SHA is the trusted main SHA, not the PR's base SHA.
        # Compare PR base SHA/ref to authenticated API inside personal_check.
        # This parser validates metadata only. Its event_name parameter is a
        # parser label, never a claim that a pull_request workflow was trusted.
        args = personal_pr_event_inputs(event, PERSONAL_REPO, 'pull_request')
        if checker is None:
            outcome = personal_check(*args, token, expected_base_ref=base_ref,
                                     expected_base_sha=base['sha'])
        else:
            # Preserves isolated injected-checker signature; CLI never passes a checker.
            outcome = checker(*args, token)
        personal_require(outcome == 'PERSONAL_APPROVAL_V1_PR_PROXY_ONLY',
                         'authenticated personal approval absent or rejected')
        print('TRUSTED_MAIN_REQUIRED PASS: GitHub owner PR-approval proxy verified')
        print('NOTE: Required-Check enforcement is owned by GitHub ruleset, not self-certified by this process.')
        return 0
    except (PersonalBlocked, OSError, UnicodeError, ValueError, TypeError,
            AttributeError, KeyError) as exc:
        print('TRUSTED_MAIN_REQUIRED BLOCK:', str(exc), file=sys.stderr)
        return 1


def main(argv):
    if len(argv) == 2 and argv[1] == '--personal-trusted-target-required':
        return personal_trusted_target_required_main()
    if len(argv) == 2 and argv[1] == "--personal-trusted-target-candidate":
        # Trusted-main metadata-only candidate, NOT an active Required Check.
        return personal_trusted_target_candidate_main()
    if len(argv) >= 2 and argv[1] == "--personal-manual":
        # Returns advisory status ONLY, not independent Required Check authority.
        return personal_main(argv[2:])
    if len(argv) == 2 and argv[1] == "--personal-pr-auto":
        # Candidate-only event adapter; no legacy verify_live() promotion.
        return personal_pr_auto_main()
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
