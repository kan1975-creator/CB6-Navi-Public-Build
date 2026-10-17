#!/usr/bin/env python3
"""Explicit CB6 guarded operation entrypoint; NOT a global GitHub write hook.

This module delegates an explicitly approved operation exactly once to
operation_bridge.apply_approved_write, now using one non-force Git ref update.
On failure it creates a private, non-authoritative local incident draft.
It is not a global GitHub write interceptor and never merges, dispatches,
updates the GitHub failure ledger, or issues a Release.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from operation_bridge import GithubCLI, apply_approved_write, propose_postcheck
from preflight import Blocked, validate_ledger, _validate_failure_record

_SHA = re.compile(r'\A[0-9a-f]{40}\Z')
_KEY = re.compile(r'\A[a-z][a-z0-9_]{2,79}\Z')
_CODE = re.compile(r'\A[A-Z][A-Z0-9_]{2,79}\Z')
_MAX_FILE = 1024 * 1024


def require(ok, reason):
    if not ok:
        raise Blocked(reason)


def read_json(path):
    p = Path(path)
    require(p.is_file() and p.stat().st_size <= _MAX_FILE, 'INVALID_INPUT_FILE')
    return json.loads(p.read_text(encoding='utf-8'))


def read_draft(path):
    p = Path(path)
    require(p.is_file() and p.stat().st_size <= _MAX_FILE, 'INVALID_CANDIDATE_FILE')
    return p.read_text(encoding='utf-8')


def _metadata(plan, candidate):
    """No untrusted exception text, credentials, or candidate content in drafts."""
    require(type(plan) is dict, 'INVALID_OPERATION_PLAN')
    require(type(candidate) is str, 'INVALID_CANDIDATE')
    path = plan.get('path')
    operation = plan.get('operation')
    expected_head = plan.get('expected_head')
    require(type(path) is str and bool(path) and len(path) <= 250 and
            type(operation) is str and operation in ('create', 'update') and
            type(expected_head) is str and bool(_SHA.fullmatch(expected_head)),
            'INVALID_OPERATION_METADATA')
    return {'path': path, 'operation': operation, 'expected_head': expected_head,
            'candidate_sha256': hashlib.sha256(candidate.encode('utf-8')).hexdigest()}


def _save_private(draft_dir, record):
    """Create one local draft, never overwrite. No GitHub side effects."""
    require(type(record) is dict, 'INVALID_DRAFT')
    dest = Path(draft_dir)
    require(dest.is_dir() and not dest.is_symlink(), 'LOCAL_DRAFT_DIR_MISSING')
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    digest = hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False,
                        separators=(',', ':')).encode('utf-8')).hexdigest()[:16]
    filename = f'cb6_pending_failure_{now}_{digest}.json'
    target = dest / filename
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, sort_keys=True, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    return target


def _failure_code(exc):
    if isinstance(exc, Blocked):
        value = str(exc)
        if _CODE.fullmatch(value):
            return value
    # Do not put arbitrary exception text in a file; could expose credentials.
    return 'UNKNOWN_FAILURE_RECONCILIATION_REQUIRED'


def run_approved(api, plan, candidate, draft_dir, *, writer=apply_approved_write):
    """One guarded write attempt and at most one local failure draft.

    All actual GitHub authentication/Ruleset/approval/digest checks are performed
    inside the existing bridge. Never retry an unknown write result automatically.
    """
    context = _metadata(plan, candidate)
    require(Path(draft_dir).is_dir() and not Path(draft_dir).is_symlink(),
            'LOCAL_DRAFT_DIR_MISSING')
    try:
        result = writer(api, plan, candidate)
        # Treat ambiguous/malformed replies as unverified outcomes requiring
        # reconciliation, never an implicit success or automatic retry.
        require(type(result) is dict and
                result.get('status') == 'WRITE_COMPLETE_NOT_MERGED' and
                type(result.get('commit_sha')) is str and
                bool(_SHA.fullmatch(result['commit_sha'])) and
                result.get('path') == context['path'] and
                result.get('candidate_sha256') == context['candidate_sha256'],
                'UNKNOWN_WRITE_RESULT_RECONCILIATION_REQUIRED')
    except Exception as exc:
        entry = {
            'schema': 1, 'type': 'LOCAL_FAILURE_DRAFT',
            'authoritative_ledger_update': False, 'verified_root_cause': False,
            'record_status': 'OWNER_REVIEW_REQUIRED',
            'failure_code': _failure_code(exc), 'operation_context': context,
            'action': 'RECONCILE_GITHUB_STATE_BEFORE_RETRY',
            'evidence': ['single explicit guarded operation attempt failed'],
        }
        local_path = _save_private(draft_dir, entry)
        return {'status': 'BLOCKED_LOCAL_DRAFT_CREATED',
                'failure_code': entry['failure_code'], 'draft_path': str(local_path),
                'github_write_verified': False, 'manual_reconciliation_required': True}
    return {'status': 'WRITE_COMPLETE_NOT_MERGED', 'commit_sha': result['commit_sha'],
            'path': context['path'], 'candidate_sha256': context['candidate_sha256'],
            'automatic_required_check_not_asserted': True}


def propose_failure(ledger, failure, draft_dir):
    """Locally record a new failure OR a known-cause recurrence; never push.

    The supplied root cause, evidence, prevention and cases must be complete to
    be considered validated *shape*; factual attribution still needs review.
    """
    validate_ledger(ledger)
    require(type(failure) is dict, 'INVALID_FAILURE_INPUT')
    key = failure.get('cause_key')
    require(type(key) is str and bool(_KEY.fullmatch(key)),
            'MISSING_STABLE_CAUSE_KEY')
    # Reject missing or malformed evidence without fabricating diagnosis.
    _validate_failure_record(failure)
    require(failure.get('status') == 'OPEN', 'FAILURE_MUST_BE_OPEN')
    outcome = propose_postcheck(ledger, failure)
    action = outcome.get('action')
    require(action in ('RECURRING_CAUSE_REVIEW_LEARNING_MECHANISM',
                       'NEW_FAILURE_PROPOSED_NOT_COMMITTED'),
            'UNKNOWN_LEARNING_RESULT')
    record = {'schema': 1, 'type': 'LOCAL_FAILURE_DRAFT',
              'authoritative_ledger_update': False,
              'verified_root_cause': False,
              'record_status': 'OWNER_REVIEW_REQUIRED', 'cause_key': key,
              'action': action, 'proposed_record': failure,
              'evidence_is_unverified_submission': True,
              'github_ledger_write_performed': False}
    if action == 'RECURRING_CAUSE_REVIEW_LEARNING_MECHANISM':
        record['existing_failure_id'] = outcome.get('existing_id')
    target = _save_private(draft_dir, record)
    return {'status': 'LOCAL_DRAFT_CREATED_NOT_ADOPTED',
            'classification': action, 'draft_path': str(target),
            'github_ledger_write_performed': False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=('apply', 'postcheck'), required=True)
    p.add_argument('--draft-dir', required=True)
    p.add_argument('--plan')
    p.add_argument('--candidate')
    p.add_argument('--ledger')
    p.add_argument('--failure')
    args = p.parse_args(argv)
    try:
        if args.mode == 'apply':
            require(args.plan is not None and args.candidate is not None and
                    args.ledger is None and args.failure is None, 'INVALID_APPLY_ARGS')
            result = run_approved(GithubCLI(), read_json(args.plan),
                                  read_draft(args.candidate), args.draft_dir)
        else:
            require(args.ledger is not None and args.failure is not None and
                    args.plan is None and args.candidate is None,
                    'INVALID_POSTCHECK_ARGS')
            result = propose_failure(read_json(args.ledger),
                                     read_json(args.failure), args.draft_dir)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result['status'] in ('WRITE_COMPLETE_NOT_MERGED',
                                        'LOCAL_DRAFT_CREATED_NOT_ADOPTED') else 2
    except (Blocked, OSError, ValueError, TypeError) as exc:
        print('BLOCK: ' + _failure_code(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
