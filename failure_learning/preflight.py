#!/usr/bin/env python3
"""CB6 read-only, fail-closed offline preflight of known failure patterns.

CANDIDATE ONLY: verifies *supplied* evidence, not its GitHub provenance.
A passing result is advisory; it cannot authorize writes, merges or Actions.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

EXPECTED = {
    'approval_provenance': 'pr_creation',
    'github_actions_log_transport': 'workflow_dispatch',
    'duplicate_pull_request_head': 'pr_merge',
    'apk_signer_output_parsing': 'apk_signature',
}
CERT_SHA256 = '0CCCC7C349BCC0005F53AA1A58F42B1C8EC6A387513F7C33576390842EAC301A'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')

class Blocked(Exception):
    pass

def require(ok, code):
    if not ok:
        raise Blocked(code)

def timestamp(value):
    require(isinstance(value, str), 'BAD_TIMESTAMP')
    try:
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise Blocked('BAD_TIMESTAMP') from None
    require(result.tzinfo is not None, 'NAIVE_TIMESTAMP')
    return result.astimezone(dt.timezone.utc)

def validate_ledger(ledger):
    require(type(ledger) is dict and ledger.get('schema') == 1 and
            ledger.get('candidate_only') is True, 'BAD_LEDGER')
    entries = ledger.get('failures')
    require(type(entries) is list and len(entries) >= len(EXPECTED), 'MISSING_FAILURE_RECORDS')
    ids = []
    for item in entries:
        require(type(item) is dict, 'BAD_FAILURE_RECORD')
        for key in ('id', 'phase', 'root_cause', 'evidence', 'affected_paths',
                    'prevention', 'regression_cases', 'status'):
            require(item.get(key) is not None, 'INCOMPLETE_FAILURE_RECORD')
        require(type(item['id']) is str and type(item['phase']) is str and
                type(item['root_cause']) is str and bool(item['root_cause']) and
                type(item['prevention']) is str and bool(item['prevention']) and
                type(item['evidence']) is list and bool(item['evidence']) and
                all(type(x) is str and bool(x) for x in item['evidence']) and
                type(item['affected_paths']) is list and bool(item['affected_paths']) and
                all(type(x) is str and bool(x) for x in item['affected_paths']) and
                type(item['regression_cases']) is list and len(item['regression_cases']) >= 2 and
                all(type(x) is str and bool(x) for x in item['regression_cases']) and
                item['status'] in ('PREVENTION_PROPOSED', 'PREVENTION_VERIFIED', 'OPEN'),
                'INVALID_FAILURE_RECORD')
        ids.append(item['id'])
    require(len(ids) == len(set(ids)) and set(ids) == set(EXPECTED),
            'MISSING_DUPLICATE_OR_UNSUPPORTED_FAILURE_ID')
    for item in entries:
        require(item['phase'] == EXPECTED[item['id']], 'WRONG_FAILURE_PHASE')

def field(value, kind):
    require(type(value) is str and bool(value), 'MISSING_' + kind)
    return value

def check_approval(e):
    require(e.get('owner_login') == 'kan1975-creator' and
            e.get('approval_author_login') == 'kan1975-creator' and
            type(e.get('approval_comment_id')) is int and e['approval_comment_id'] > 0,
            'NO_OWNER_APPROVAL')
    plan_sha = field(e.get('plan_sha256'), 'PLAN_SHA')
    basis_sha = field(e.get('plan_basis_head'), 'PLAN_BASIS')
    require(bool(SHA64.fullmatch(plan_sha)) and bool(SHA40.fullmatch(basis_sha)) and
            e.get('pr_base_sha') == basis_sha, 'PLAN_PR_BASE_MISMATCH')
    require(timestamp(e.get('plan_committed_at')) < timestamp(e.get('approval_created_at')) <
            timestamp(e.get('pr_created_at')), 'APPROVAL_NOT_BEFORE_PR')
    require(e.get('approval_updated_at') == e.get('approval_created_at') and
            e.get('plan_path_in_pr') is True and e.get('approval_ref_in_pr') is True,
            'APPROVAL_EDITED_OR_UNBOUND')

def check_logs(e):
    require(e.get('gh_api_log_command') == 'gh api --allow-escape-sequences',
            'UNSAFE_GH_LOG_DOWNLOAD')
    require(e.get('retrieved_log_has_expected_failure') is True,
            'OLD_RUN_LOG_UNVERIFIED')
    runs = e.get('historical_run_ids')
    require(type(runs) is list and len(runs) > 0 and
            all(type(x) is int and x > 0 for x in runs) and len(set(runs)) == len(runs),
            'INVALID_RUN_HISTORY')
    require(e.get('attempt') == 1 and type(e.get('new_run_id')) is int and
            e['new_run_id'] not in runs and e.get('history_complete') is True,
            'RERUN_OR_INCOMPLETE_HISTORY')

def check_merge(e):
    current = field(e.get('target_pr_head_sha'), 'TARGET_HEAD')
    require(bool(SHA40.fullmatch(current)), 'BAD_TARGET_HEAD')
    other = e.get('other_open_pr_heads')
    require(type(other) is list and all(type(x) is str and SHA40.fullmatch(x) for x in other),
            'INCOMPLETE_OPEN_PR_HEADS')
    require(e.get('all_pr_pages_fetched') is True and e.get('expected_base_sha') ==
            e.get('actual_base_sha') and bool(SHA40.fullmatch(field(e.get('actual_base_sha'),'BASE_SHA'))),
            'STALE_OR_UNTRUSTED_PR_SNAPSHOT')
    require(current not in other, 'DUPLICATE_HEAD_MERGE_SIDE_EFFECT')

def check_signature(e):
    output = field(e.get('apksigner_output'), 'APK_SIGNER_OUTPUT')
    lines = output.splitlines()
    v2 = [s for s in lines if s.startswith('Verified using v2 scheme (APK Signature Scheme v2): ')]
    count = [s for s in lines if s.startswith('Number of signers: ')]
    digest = [s for s in lines if s.startswith('V2 Signer: certificate SHA-256 digest: ')]
    require(v2 == ['Verified using v2 scheme (APK Signature Scheme v2): true'], 'V2_NOT_VERIFIED')
    require(count == ['Number of signers: 1'], 'INVALID_SIGNER_COUNT')
    require(len(digest) == 1, 'MISSING_OR_MULTIPLE_SIGNER_CERTIFICATES')
    match = re.fullmatch(r'V2 Signer: certificate SHA-256 digest: ([0-9a-fA-F]{64})', digest[0])
    require(match is not None and match.group(1).upper() == CERT_SHA256,
            'CANONICAL_SIGNER_SHA256_MISMATCH_OR_MISSING')

def evaluate(ledger, evidence):
    validate_ledger(ledger)
    require(type(evidence) is dict, 'BAD_EVIDENCE')
    phase = evidence.get('phase')
    checks = {
        'pr_creation': check_approval,
        'workflow_dispatch': check_logs,
        'pr_merge': check_merge,
        'apk_signature': check_signature,
    }
    require(phase in checks, 'UNKNOWN_OR_UNSUPPORTED_PHASE')
    checks[phase](evidence)
    return 'OFFLINE_PREFLIGHT_PASS_NOT_AUTHORIZATION'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=Path(__file__).with_name('failures_v1.json'))
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding='utf-8'))
        evidence = json.loads(args.evidence.read_text(encoding='utf-8'))
        print(evaluate(ledger, evidence))
    except (Blocked, OSError, ValueError, TypeError) as exc:
        print('BLOCK: ' + str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
