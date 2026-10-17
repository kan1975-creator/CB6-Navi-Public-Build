#!/usr/bin/env python3
"""CB6 opt-in, fail-closed file-write bridge and postcheck failure proposer.

Opt-in Git object writer with GraphQL updateRefs atomic beforeOid CAS.
A caller must explicitly route an approved write through apply_approved_write();
unrouted writes bypass this bridge. It NEVER merges, dispatches, or releases.
Concurrent advances fail at atomic old-HEAD compare-and-swap without retry.
"""
import base64
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import PurePosixPath

from preflight import Blocked, learn_failure, prewrite_review, validate_ledger

OWNER = 'kan1975-creator'
OWNER_ID = 313684924
REPO = 'kan1975-creator/CB6-Navi-Public-Build'
RULESET = 24792110
CHECK = 'cb6-personal-approval-trusted-candidate'
APP_ID = 15368
REQUIRED_FIELDS = frozenset({
    'repository', 'pr_number', 'branch', 'expected_head', 'fixed_main_head',
    'path', 'operation', 'approved_paths', 'candidate_sha256',
    'approval_comment_id', 'owner_login', 'owner_id'
})
SHA40 = re.compile(r'\A[0-9a-f]{40}\Z')
SHA64 = re.compile(r'\A[0-9a-f]{64}\Z')


def atomic_update_key(branch, before_oid, after_oid):
    return hashlib.sha256((REPO + '\n' + branch + '\n' + before_oid + '\n' +
                           after_oid).encode('utf-8')).hexdigest()


def insist(condition, reason):
    if not condition:
        raise Blocked(reason)


def canonical_plan_sha(plan):
    # GitHub assigns this locator only after the unedited approval is posted.
    # Bind all operation fields first; attach the locator after posting.
    approved = {k: v for k, v in plan.items() if k != 'approval_comment_id'}
    return hashlib.sha256(json.dumps(approved, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def plan_binding(plan):
    """The owner-authored GitHub comment must contain this exact plan digest."""
    return 'CB6-BRIDGE-PLAN-SHA256 ' + canonical_plan_sha(plan)


def safe_path(value):
    insist(type(value) is str and value and not value.startswith('/') and
           not value.endswith('/') and re.fullmatch(r'[A-Za-z0-9_./-]+', value) and
           str(PurePosixPath(value)) == value and
           all(p not in ('', '.', '..') for p in value.split('/')),
           'INVALID_REPOSITORY_PATH')
    insist(not (value.startswith('v2/') or value.startswith('.github/') or
                value == 'PUBLIC_BUILD_NOTICE.md'), 'FROZEN_PATH')
    return value


def check_plan(plan, candidate):
    insist(type(plan) is dict and set(plan) == REQUIRED_FIELDS,
           'UNEXPECTED_OR_MISSING_PLAN_FIELD')
    insist(plan['repository'] == REPO and plan['owner_login'] == OWNER and
           type(plan['owner_id']) is int and plan['owner_id'] == OWNER_ID,
           'WRONG_REPOSITORY_OR_OWNER')
    insist(type(plan['pr_number']) is int and plan['pr_number'] >= 1,
           'INVALID_PR_NUMBER')
    insist(type(plan['branch']) is str and plan['branch'].startswith('feature/')
           and re.fullmatch(r'[A-Za-z0-9_./-]+', plan['branch']) and
           '..' not in plan['branch'] and not plan['branch'].endswith('/'),
           'UNAPPROVED_BRANCH')
    insist(type(plan['expected_head']) is str and SHA40.fullmatch(plan['expected_head'])
           and type(plan['fixed_main_head']) is str and
           SHA40.fullmatch(plan['fixed_main_head']), 'INVALID_HEAD')
    insist(type(candidate) is str, 'INVALID_CANDIDATE')
    insist(type(plan['approved_paths']) is list and plan['approved_paths'] and
           len(plan['approved_paths']) == len(set(plan['approved_paths'])),
           'BAD_APPROVED_PATHS')
    for p in plan['approved_paths']:
        safe_path(p)
    insist(safe_path(plan['path']) in plan['approved_paths'] and
           plan['operation'] in ('create', 'update'), 'OPERATION_NOT_APPROVED')
    insist(type(plan['approval_comment_id']) is int and plan['approval_comment_id'] > 0,
           'MISSING_APPROVAL_COMMENT')
    insist(type(plan['candidate_sha256']) is str and
           SHA64.fullmatch(plan['candidate_sha256']) and
           hashlib.sha256(candidate.encode('utf-8')).hexdigest() ==
           plan['candidate_sha256'], 'CANDIDATE_DIGEST_MISMATCH')


def authenticated_evidence(api, plan):
    """Read live GitHub provenance; do not trust caller-supplied evidence JSON."""
    user = api.get('user')
    insist(user.get('login') == OWNER and user.get('id') == OWNER_ID,
           'WRONG_AUTHENTICATED_ACTOR')
    root = 'repos/' + REPO + '/'
    main = api.get(root + 'branches/main')
    insist(main.get('commit', {}).get('sha') == plan['fixed_main_head'] and
           main.get('protected') is True, 'MAIN_CHANGED_OR_UNPROTECTED')
    branch = api.get(root + 'branches/' + plan['branch'])
    insist(branch.get('commit', {}).get('sha') == plan['expected_head'],
           'BRANCH_HEAD_CHANGED')
    pr = api.get(root + 'pulls/' + str(plan['pr_number']))
    insist(pr.get('state') == 'open' and pr.get('merged_at') is None and
           pr.get('head', {}).get('sha') == plan['expected_head'] and
           pr.get('head', {}).get('ref') == plan['branch'] and
           pr.get('base', {}).get('sha') == plan['fixed_main_head'],
           'PR_HEAD_BASE_OR_STATE_MISMATCH')
    rules = api.get(root + 'rulesets/' + str(RULESET))
    insist(rules.get('enforcement') == 'active' and rules.get('bypass_actors') == [] and
           rules.get('target') == 'branch' and
           rules.get('conditions', {}).get('ref_name', {}).get('exclude') == [] and
           {'refs/heads/main', 'refs/heads/cb6-v2-clean'}.issubset(set(
               rules.get('conditions', {}).get('ref_name', {}).get('include', []))),
           'RULESET_INACTIVE_OR_BYPASS')
    insist({'pull_request', 'deletion', 'non_fast_forward'}.issubset(
               {rule.get('type') for rule in rules.get('rules', [])}),
           'RULESET_REQUIRED_PROTECTION_MISSING')
    required = [s for rule in rules.get('rules', [])
                if rule.get('type') == 'required_status_checks'
                for s in rule.get('parameters', {}).get('required_status_checks', [])]
    insist(any(s.get('context') == CHECK and s.get('integration_id') == APP_ID
               for s in required), 'REQUIRED_CHECK_NOT_CONFIGURED')
    c = api.get(root + 'issues/comments/' + str(plan['approval_comment_id']))
    insist(type(c.get('id')) is int and c['id'] == plan['approval_comment_id'] and
           c.get('user', {}).get('login') == OWNER and
           c.get('user', {}).get('id') == OWNER_ID and
           c.get('issue_url') == 'https://api.github.com/' + root +
           'issues/11' and
           c.get('created_at') and c.get('created_at') == c.get('updated_at') and
           plan_binding(plan) in c.get('body', '').splitlines(),
           'OWNER_APPROVAL_UNVERIFIED')
    dt.datetime.fromisoformat(c['created_at'].replace('Z', '+00:00'))
    return root


def decode_contents(record):
    insist(record.get('encoding') == 'base64' and
           type(record.get('content')) is str, 'NON_BASE64_CONTENT')
    try:
        return base64.b64decode(''.join(record['content'].split()), validate=True).decode('utf-8')
    except (ValueError, UnicodeError) as exc:
        raise Blocked('CONTENT_DECODE_ERROR') from exc


def apply_approved_write(api, plan, candidate):
    """Sole opt-in write entrypoint; API must implement get() and put().

    The successful preflight is NOT itself an owner approval. Owner identity,
    plan-bound unedited comment, immutable draft hash, PR and Ruleset are read
    independently from GitHub immediately before the explicit write.
    """
    check_plan(plan, candidate)
    root = authenticated_evidence(api, plan)
    ledger_obj = api.get(root + 'contents/failure_learning/failures_v1.json?ref=' +
                         plan['expected_head'])
    ledger = json.loads(decode_contents(ledger_obj))
    validate_ledger(ledger)
    result = prewrite_review(ledger, {
        'path': plan['path'], 'approved_paths': plan['approved_paths'],
        'operation': plan['operation'], 'fixed_main_head': plan['fixed_main_head'],
        'observed_main_head': plan['fixed_main_head'],
        'candidate_sha256': plan['candidate_sha256']
    }, candidate)
    insist(result['status'] == 'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION'
           and result['candidate_sha256'] == plan['candidate_sha256'],
           'PREFLIGHT_UNRESOLVED_OR_MISMATCH')
    endpoint = root + 'contents/' + plan['path']
    existing = api.get_optional(endpoint + '?ref=' + plan['branch'])
    if plan['operation'] == 'create':
        insist(existing is None, 'FILE_ALREADY_EXISTS')
    else:
        insist(type(existing) is dict and SHA40.fullmatch(existing.get('sha', '')),
               'MISSING_UPDATE_BLOB_SHA')
    # Resolve the server-owned GraphQL repository identity; never accept a
    # caller-provided ID for the atomic mutation.
    repository = api.get(root[:-1])
    insist(type(repository) is dict and repository.get('full_name') == REPO and
           type(repository.get('node_id')) is str and
           bool(repository['node_id']), 'GRAPHQL_REPOSITORY_ID_UNVERIFIED')
    repository_id = repository['node_id']
    # Git objects are staged under an immutable expected parent only.
    authenticated_evidence(api, plan)
    parent = api.get(root + 'git/commits/' + plan['expected_head'])
    parent_tree = parent.get('tree', {}).get('sha')
    insist(type(parent_tree) is str and SHA40.fullmatch(parent_tree),
           'EXPECTED_PARENT_TREE_MISSING')
    blob = api.post(root + 'git/blobs', {
        'content': base64.b64encode(candidate.encode('utf-8')).decode('ascii'),
        'encoding': 'base64'})
    blob_sha = blob.get('sha')
    insist(type(blob_sha) is str and SHA40.fullmatch(blob_sha),
           'BLOB_CREATION_UNVERIFIED_RECONCILE')
    tree = api.post(root + 'git/trees', {
        'base_tree': parent_tree,
        'tree': [{'path': plan['path'], 'mode': '100644',
                  'type': 'blob', 'sha': blob_sha}]})
    tree_sha = tree.get('sha')
    insist(type(tree_sha) is str and SHA40.fullmatch(tree_sha),
           'TREE_CREATION_UNVERIFIED_RECONCILE')
    proposal = api.post(root + 'git/commits', {
        'message': 'cb6: owner-approved guarded atomic file write',
        'tree': tree_sha, 'parents': [plan['expected_head']]})
    commit = proposal.get('sha')
    insist(type(commit) is str and SHA40.fullmatch(commit),
           'COMMIT_CREATION_UNVERIFIED_RECONCILE')
    insist(type(proposal.get('parents')) is list and
           [p.get('sha') for p in proposal['parents']] == [plan['expected_head']],
           'COMMIT_PARENT_MISMATCH')
    # Never retry unknown results; even a successful staging call is not
    # proof that the branch ref has moved.
    authenticated_evidence(api, plan)
    current = api.get(root + 'branches/' + plan['branch'])
    insist(current.get('commit', {}).get('sha') == plan['expected_head'],
           'BRANCH_HEAD_CHANGED')
    # REST force=false is NOT atomic with the preceding read. GraphQL's
    # beforeOid condition is evaluated atomically with this ref mutation.
    answer = api.atomic_ref_update(repository_id, plan['branch'],
                                   plan['expected_head'], commit)
    expected_key = atomic_update_key(plan['branch'], plan['expected_head'], commit)
    insist(type(answer) is dict and not answer.get('errors') and
           type(answer.get('data')) is dict and
           type(answer['data'].get('updateRefs')) is dict and
           answer['data']['updateRefs'].get('clientMutationId') == expected_key,
           'ATOMIC_REF_UPDATE_UNVERIFIED_RECONCILE')
    branch_after = api.get(root + 'branches/' + plan['branch'])
    insist(branch_after.get('commit', {}).get('sha') == commit,
           'POSTWRITE_BRANCH_MISMATCH_RECONCILE')
    after = api.get(root + 'contents/' + plan['path'] + '?ref=' + commit)
    insist(after.get('sha') == blob_sha and decode_contents(after) == candidate,
           'POSTWRITE_FILE_MISMATCH_RECONCILE')
    return {'status': 'WRITE_COMPLETE_NOT_MERGED', 'commit_sha': commit,
            'path': plan['path'], 'candidate_sha256': plan['candidate_sha256']}


def propose_postcheck(ledger, failure):
    """Return a memory-only record proposal; never mutate the GitHub ledger."""
    return learn_failure(ledger, failure)


class GithubCLI:
    """Explicit, non-shell GitHub CLI adapter. No background actions."""
    def _call(self, args, data=None):
        try:
            cp = subprocess.run(['gh', 'api', *args], input=data, text=True,
                                capture_output=True, check=False, timeout=30)
        except subprocess.TimeoutExpired as exc:
            raise Blocked('GITHUB_API_TIMEOUT_RECONCILE') from exc
        insist(cp.returncode == 0, 'GITHUB_API_ERROR_NO_WRITE_OR_RECONCILE')
        try:
            return json.loads(cp.stdout)
        except json.JSONDecodeError as exc:
            raise Blocked('GITHUB_JSON_INVALID') from exc

    def get(self, endpoint):
        return self._call([endpoint])

    def get_optional(self, endpoint):
        # Fail closed on all failures except an authenticated HTTP 404.
        try:
            cp = subprocess.run(['gh', 'api', '--include', endpoint], text=True,
                                capture_output=True, check=False, timeout=30)
        except subprocess.TimeoutExpired as exc:
            raise Blocked('CONTENT_LOOKUP_TIMEOUT_RECONCILE') from exc
        headers, separator, body = cp.stdout.partition('\r\n\r\n')
        if not separator:
            headers, separator, body = cp.stdout.partition('\n\n')
        insist(bool(separator), 'UNKNOWN_CONTENT_LOOKUP_RESULT')
        first = headers.splitlines()[0]
        if ' 404 ' in first:
            return None
        insist(cp.returncode == 0 and ' 200 ' in first, 'CONTENT_LOOKUP_FAILED')
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise Blocked('GITHUB_JSON_INVALID') from exc

    def post(self, endpoint, data):
        return self._call(['--method', 'POST', endpoint, '--input', '-'],
                          json.dumps(data, sort_keys=True))

    def atomic_ref_update(self, repository_id, branch, before_oid, after_oid):
        """Exactly one GraphQL CAS mutation, with no fallback and no retry."""
        insist(type(repository_id) is str and bool(repository_id) and
               type(branch) is str and branch.startswith('feature/') and
               type(before_oid) is str and SHA40.fullmatch(before_oid) and
               type(after_oid) is str and SHA40.fullmatch(after_oid),
               'INVALID_ATOMIC_UPDATE_ARGUMENTS')
        query = ('mutation CB6AtomicUpdate($input: UpdateRefsInput!) {'
                 ' updateRefs(input: $input) { clientMutationId } }')
        body = {'query': query, 'variables': {'input': {
            'repositoryId': repository_id,
            'clientMutationId': atomic_update_key(branch, before_oid, after_oid),
            'refUpdates': [{'name': 'refs/heads/' + branch,
                            'beforeOid': before_oid, 'afterOid': after_oid,
                            'force': False}]}}}
        return self._call(['graphql', '--input', '-'],
                          json.dumps(body, sort_keys=True))


if __name__ == '__main__':
    # Opt-in CLI: no automatic writing, even after importing this file.
    import argparse
    import sys
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=('apply', 'postcheck'), required=True)
    p.add_argument('--plan', help='Exact approved JSON plan for apply')
    p.add_argument('--candidate', help='Draft text file for apply')
    p.add_argument('--ledger', help='Failure ledger JSON for postcheck')
    p.add_argument('--failure', help='Validated failure record JSON for postcheck')
    a = p.parse_args()
    try:
        if a.mode == 'apply':
            insist(a.plan is not None and a.candidate is not None,
                   'MISSING_PLAN_OR_CANDIDATE')
            plan = json.load(open(a.plan, encoding='utf-8'))
            draft = open(a.candidate, encoding='utf-8').read()
            report = apply_approved_write(GithubCLI(), plan, draft)
        else:
            insist(a.ledger is not None and a.failure is not None,
                   'MISSING_LEDGER_OR_FAILURE')
            report = propose_postcheck(json.load(open(a.ledger, encoding='utf-8')),
                                       json.load(open(a.failure, encoding='utf-8')))
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    except (Blocked, ValueError, OSError, TypeError) as exc:
        print('BLOCK: ' + str(exc), file=sys.stderr)
        sys.exit(2)
