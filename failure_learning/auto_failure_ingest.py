#!/usr/bin/env python3
"""Inert-until-authorized failure capture for trusted workflow_run events.

Only verified numeric IDs and fixed labels enter a pending Issue comment.
No logs, PR-controlled text, credentials, unverified diagnosis or ledger writes.
A separately approved owner comment and explicit repository variables are
required for actual persistence after the workflow is deployed.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys

REPO = 'kan1975-creator/CB6-Navi-Public-Build'
OWNER = 'kan1975-creator'
OWNER_ID = 313684924
PLAN_SHA = '663a09ef661282c2d0dafcbf73ffac23b99ea0cb4aaecc279c0ed95454230bd3'
TRUSTED_WORKFLOW_ID = 383229001
TRUSTED_WORKFLOW_NAME = 'CB6 Personal Approval Trusted Main Candidate'
FAILURE_CODE = 'CB6_TRUSTED_APPROVAL_JOB_FAILED'
RULESET = 24792110
CHECK = 'cb6-personal-approval-trusted-candidate'
APP_ID = 15368
POSITIVE_ID = re.compile(r'^[1-9][0-9]{0,15}$')
MAX_PAGES = 30


class Blocked(Exception):
    pass


def insist(ok, reason):
    if not ok:
        raise Blocked(reason)


def numeric(value):
    insist(type(value) is str and bool(POSITIVE_ID.fullmatch(value)),
           'INVALID_POSITIVE_IDENTIFIER')
    return int(value)


def get_repo(api, path):
    record = api.get('repos/' + REPO + '/' + path)
    insist(type(record) is dict, 'INVALID_GITHUB_RESPONSE')
    return record


def pages(api, path):
    rows = []
    for n in range(1, MAX_PAGES + 1):
        sep = '&' if '?' in path else '?'
        batch = api.get('repos/' + REPO + '/' + path +
                        sep + f'per_page=100&page={n}')
        insist(type(batch) is list and len(batch) <= 100,
               'INVALID_OR_TRUNCATED_PAGE')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
    raise Blocked('PAGINATION_INCOMPLETE')


def verify_capture_ruleset(rules):
    """Fail closed unless the live branch policy enforces PR and trusted check."""
    insist(type(rules) is dict and rules.get('enforcement') == 'active' and
           rules.get('target') == 'branch' and
           rules.get('bypass_actors') == [] and
           rules.get('current_user_can_bypass') == 'never',
           'RULESET_UNVERIFIED')
    conditions = rules.get('conditions')
    insist(type(conditions) is dict and
           type(conditions.get('ref_name')) is dict,
           'RULESET_CONDITIONS_INVALID')
    ref_name = conditions['ref_name']
    includes = ref_name.get('include')
    insist(type(includes) is list and
           all(type(x) is str for x in includes) and
           {'refs/heads/main', 'refs/heads/cb6-v2-clean'}.issubset(set(includes)) and
           ref_name.get('exclude') == [], 'RULESET_REF_SCOPE_UNVERIFIED')
    rules_list = rules.get('rules')
    insist(type(rules_list) is list and all(type(r) is dict for r in rules_list),
           'RULESET_RULES_INVALID')
    by_type = {}
    for rule in rules_list:
        kind = rule.get('type')
        insist(type(kind) is str and kind not in by_type,
               'RULESET_DUPLICATE_OR_INVALID_RULE')
        by_type[kind] = rule
    insist({'deletion', 'non_fast_forward', 'pull_request',
            'required_status_checks'}.issubset(by_type),
           'RULESET_REQUIRED_PROTECTION_MISSING')
    pr = by_type['pull_request'].get('parameters')
    insist(type(pr) is dict and
           type(pr.get('required_approving_review_count')) is int and
           pr['required_approving_review_count'] >= 0 and
           pr.get('require_extra_approval_for_unattributed_changes') is True and
           type(pr.get('allowed_merge_methods')) is list and
           bool(pr['allowed_merge_methods']) and
           all(x in ('merge', 'rebase', 'squash') for x in pr['allowed_merge_methods']),
           'PULL_REQUEST_PROTECTION_UNVERIFIED')
    params = by_type['required_status_checks'].get('parameters')
    insist(type(params) is dict and
           type(params.get('strict_required_status_checks_policy')) is bool and
           params.get('do_not_enforce_on_create') is False and
           type(params.get('required_status_checks')) is list,
           'REQUIRED_CHECK_PARAMETERS_UNVERIFIED')
    checks = params['required_status_checks']
    insist(all(type(c) is dict and type(c.get('context')) is str and
               type(c.get('integration_id')) is int for c in checks),
           'REQUIRED_CHECK_ENTRY_INVALID')
    selected = [c for c in checks if c['context'] == CHECK]
    insist(len(selected) == 1 and selected[0]['integration_id'] == APP_ID,
           'REQUIRED_CHECK_NAME_OR_APP_MISMATCH')


def authorization(api, issue_id, comment_id):
    # An Actions token is not impersonation of the owner; an unedited
    # owner-authored, plan-bound comment supplies authorization evidence.
    main = get_repo(api, 'branches/main')
    clean = get_repo(api, 'branches/cb6-v2-clean')
    insist(main.get('protected') is True and clean.get('protected') is True,
           'PROTECTED_BRANCH_UNVERIFIED')
    verify_capture_ruleset(get_repo(api, 'rulesets/' + str(RULESET)))
    issue = get_repo(api, 'issues/' + str(issue_id))
    insist(issue.get('number') == issue_id and issue.get('state') == 'open' and
           'pull_request' not in issue and
           issue.get('user', {}).get('id') == OWNER_ID,
           'DESTINATION_NOT_OWNER_APPROVED_ISSUE')
    comment = get_repo(api, 'issues/comments/' + str(comment_id))
    insist(comment.get('id') == comment_id and
           comment.get('user', {}).get('login') == OWNER and
           comment.get('user', {}).get('id') == OWNER_ID and
           comment.get('created_at') and
           comment.get('created_at') == comment.get('updated_at') and
           comment.get('issue_url') ==
             'https://api.github.com/repos/' + REPO + '/issues/11' and
           comment.get('body') ==
             f'CB6-CAPTURE-ACTIVATE {PLAN_SHA} {issue_id}',
           'CAPTURE_NOT_SEPARATELY_APPROVED')


def failed_job(api, run_id, attempt):
    run = get_repo(api, 'actions/runs/' + str(run_id))
    insist(run.get('id') == run_id and run.get('run_attempt') == attempt and
           run.get('workflow_id') == TRUSTED_WORKFLOW_ID and
           run.get('name') == TRUSTED_WORKFLOW_NAME and
           run.get('event') == 'pull_request_target' and
           run.get('status') == 'completed' and run.get('conclusion') == 'failure' and
           run.get('repository', {}).get('full_name') == REPO and
           run.get('head_repository', {}).get('full_name') == REPO and
           bool(re.fullmatch(r'[0-9a-f]{40}', run.get('head_sha') or '')),
           'UNTRUSTED_OR_NOT_FAILED_RUN')
    jobs = pages(api, f'actions/runs/{run_id}/jobs?filter=all')
    failed = sorted((j['id'] for j in jobs if type(j) is dict and
                     type(j.get('id')) is int and j.get('run_id') == run_id and
                     j.get('run_attempt') == attempt and
                     j.get('status') == 'completed' and
                     j.get('conclusion') == 'failure'))
    insist(failed and len(set(failed)) == len(failed),
           'FAILED_JOB_NOT_VERIFIED')
    return failed[0], run['head_sha']


def capture(api, *, run_id, attempt, issue_id, approval_comment_id):
    """At most one POST; never retry an unknown result or adopt the ledger."""
    insist(all(type(v) is int and v > 0 for v in
               (run_id, attempt, issue_id, approval_comment_id)),
           'INVALID_IDENTIFIER')
    authorization(api, issue_id, approval_comment_id)
    job_id, head = failed_job(api, run_id, attempt)
    key = hashlib.sha256(json.dumps([run_id, attempt, job_id, FAILURE_CODE],
                          separators=(',', ':')).encode()).hexdigest()
    marker = 'CB6-PENDING-FAILURE-ID ' + key
    old = pages(api, f'issues/{issue_id}/comments')
    insist(all(type(item) is dict and type(item.get('body')) is str
               for item in old), 'UNVERIFIED_EXISTING_COMMENTS')
    if any(marker in item['body'].splitlines() for item in old):
        return {'status': 'ALREADY_RECORDED_NOT_REPOSTED', 'key': key}
    body = '\n'.join((marker,
        'CB6-RECORD-STATUS PENDING_OWNER_REVIEW_NOT_ADOPTED',
        'CB6-ROOT-CAUSE UNVERIFIED',
        'CB6-AUTHORITATIVE-LEDGER-UPDATED false',
        f'CB6-PLAN-SHA256 {PLAN_SHA}',
        f'CB6-RUN-ID {run_id}', f'CB6-RUN-ATTEMPT {attempt}',
        f'CB6-JOB-ID {job_id}', f'CB6-FAILURE-CODE {FAILURE_CODE}',
        f'CB6-TRUSTED-HEAD {head}'))
    authorization(api, issue_id, approval_comment_id)
    posted = api.post('repos/' + REPO + f'/issues/{issue_id}/comments',
                      {'body': body})
    insist(type(posted) is dict and type(posted.get('id')) is int and
           posted['id'] > 0, 'POST_OUTCOME_UNKNOWN_STOP_NO_RETRY')
    confirmed = get_repo(api, 'issues/comments/' + str(posted['id']))
    insist(confirmed.get('id') == posted['id'] and
           confirmed.get('body') == body,
           'POST_CONFIRMATION_UNVERIFIED_STOP_NO_RETRY')
    return {'status': 'PENDING_RECORD_PERSISTED_NOT_ADOPTED',
            'key': key, 'comment_id': posted['id']}


class CLI:
    def _call(self, args, obj=None):
        try:
            proc = subprocess.run(['gh', 'api', *args],
                                  input=None if obj is None else json.dumps(obj),
                                  capture_output=True, text=True,
                                  check=False, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Blocked('GITHUB_CALL_UNKNOWN_STOP_NO_RETRY') from exc
        insist(proc.returncode == 0, 'GITHUB_CALL_FAILED_STOP_NO_RETRY')
        try:
            return json.loads(proc.stdout)
        except ValueError as exc:
            raise Blocked('GITHUB_RESPONSE_INVALID') from exc

    def get(self, path):
        return self._call([path])

    def post(self, path, obj):
        return self._call(['--method', 'POST', path, '--input', '-'], obj)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    p.add_argument('--attempt', required=True)
    p.add_argument('--issue-id', required=True)
    p.add_argument('--approval-comment-id', required=True)
    a = p.parse_args(argv)
    try:
        result = capture(CLI(), run_id=numeric(a.run_id),
            attempt=numeric(a.attempt), issue_id=numeric(a.issue_id),
            approval_comment_id=numeric(a.approval_comment_id))
        print(json.dumps(result, sort_keys=True))
        return 0
    except Blocked as exc:
        print('BLOCK: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
