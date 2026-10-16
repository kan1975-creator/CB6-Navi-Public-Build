#!/usr/bin/env python3
"""CB6 read-only, fail-closed offline preflight of known failure patterns.

CANDIDATE ONLY: verifies *supplied* evidence, not its GitHub provenance.
A passing result is advisory; it cannot authorize writes, merges or Actions.
"""
import argparse
import hashlib
import copy
import datetime as dt
import json
import re
import shlex
import sys
from pathlib import Path, PurePosixPath

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

def _validate_failure_record(item):
    require(type(item) is dict, 'BAD_FAILURE_RECORD')
    for key in ('id', 'phase', 'root_cause', 'evidence', 'affected_paths',
                'prevention', 'regression_cases', 'status'):
        require(item.get(key) is not None, 'INCOMPLETE_FAILURE_RECORD')
    require(type(item['id']) is str and type(item['phase']) is str and
            bool(item['phase'].strip()) and
            type(item['root_cause']) is str and bool(item['root_cause'].strip()) and
            type(item['prevention']) is str and bool(item['prevention'].strip()) and
            type(item['evidence']) is list and bool(item['evidence']) and
            all(type(x) is str and bool(x.strip()) for x in item['evidence']) and
            type(item['affected_paths']) is list and bool(item['affected_paths']) and
            all(type(x) is str and bool(x.strip()) for x in item['affected_paths']) and
            type(item['regression_cases']) is list and len(item['regression_cases']) >= 2 and
            all(type(x) is str and bool(x.strip()) for x in item['regression_cases']) and
            item['status'] in ('PREVENTION_PROPOSED', 'PREVENTION_VERIFIED', 'OPEN'),
            'INVALID_FAILURE_RECORD')

def validate_ledger(ledger):
    require(type(ledger) is dict and ledger.get('schema') == 1 and
            ledger.get('candidate_only') is True, 'BAD_LEDGER')
    entries = ledger.get('failures')
    require(type(entries) is list and len(entries) >= len(EXPECTED), 'MISSING_FAILURE_RECORDS')
    ids = []
    for item in entries:
        _validate_failure_record(item)
        ids.append(item['id'])
    require(len(ids) == len(set(ids)) and set(EXPECTED).issubset(set(ids)),
            'MISSING_OR_DUPLICATE_FAILURE_ID')
    keys = [item.get('cause_key', item['id']) for item in entries]
    require(len(keys) == len(set(keys)) and
            all(type(k) is str and bool(k.strip()) for k in keys),
            'DUPLICATE_OR_MISSING_ROOT_CAUSE_KEY')
    for item in entries:
        require(type(item['phase']) is str and bool(item['phase'].strip()),
                'INVALID_FAILURE_PHASE')
        if item['id'] in EXPECTED:
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

def _safe_repo_path(path):
    require(type(path) is str and bool(path), 'INVALID_CANDIDATE_PATH')
    p = PurePosixPath(path)
    require(not p.is_absolute() and path == p.as_posix() and
            not any(x in ('..', '.') for x in path.split('/')) and
            not path.startswith('/') and not path.endswith('/'), 'INVALID_CANDIDATE_PATH')
    return path

def _mask_command_substitutions(source):
    """Return shell text with active $(...) masked plus nested commands to check.

    Single-quoted and escaped substitutions are literal, double-quoted ones
    execute.  A malformed substitution fails closed rather than being skipped.
    """
    def _substitution_open_after(text, pos):
        # Bash removes backslash-newline BEFORE recognizing a $() command.
        # E.g. "$\\\n(gh api .../logs)" still executes the gh command.
        if text[pos] != '$':
            return None
        j = pos + 1
        while text.startswith('\\\n', j):
            j += 2
        return j + 1 if j < len(text) and text[j] == '(' else None

    def closing_paren(start):
        quote = None
        escape = False
        comment = False
        word_boundary = True
        group_depth = 0
        i = start
        while i < len(source):
            ch = source[i]
            if comment:
                if ch == '\n':
                    comment = False
                    word_boundary = True
                i += 1
                continue
            if escape:
                escape = False
                word_boundary = False
                i += 1
                continue
            if ch == '\\' and quote != "'":
                escape = True
                i += 1
                continue
            if ch == '#' and quote is None and word_boundary:
                comment = True
                i += 1
                continue
            opener = _substitution_open_after(source, i) if quote != "'" else None
            if opener is not None:
                i = closing_paren(opener) + 1
                word_boundary = False
                continue
            if ch == "'" and quote != '"':
                quote = None if quote == "'" else "'"
            elif ch == '"' and quote != "'":
                quote = None if quote == '"' else '"'
            elif quote is None and ch == '(':
                group_depth += 1
            elif quote is None and ch == ')':
                if group_depth == 0:
                    return i
                group_depth -= 1
            word_boundary = ch.isspace() or (quote is None and ch in ';|&()')
            i += 1
        raise Blocked('UNPARSEABLE_WORKFLOW_SHELL_SUBSTITUTION')

    result = []
    substitutions = []
    quote = None
    escaped = False
    comment = False
    word_boundary = True
    i = 0
    while i < len(source):
        ch = source[i]
        if comment:
            result.append(ch)
            if ch == '\n':
                comment = False
                word_boundary = True
            i += 1
            continue
        if escaped:
            result.append(ch)
            escaped = False
            word_boundary = False
            i += 1
            continue
        if ch == '\\' and quote != "'":
            result.append(ch)
            escaped = True
            i += 1
            continue
        if ch == '#' and quote is None and word_boundary:
            comment = True
            result.append(ch)
            i += 1
            continue
        opener = _substitution_open_after(source, i) if quote != "'" else None
        if opener is not None:
            end = closing_paren(opener)
            substitutions.append(source[opener:end])
            result.append('CB6_COMMAND_SUBSTITUTION')
            i = end + 1
            word_boundary = False
            continue
        if ch == "'" and quote != '"':
            quote = None if quote == "'" else "'"
        elif ch == '"' and quote != "'":
            quote = None if quote == '"' else '"'
        result.append(ch)
        word_boundary = ch.isspace() or (quote is None and ch in ';|&()')
        i += 1
    return ''.join(result), substitutions


def _gh_log_flag_active(args):
    """Do not treat --jq's value as a gh CLI flag."""
    value_flags = {'--jq', '-q'}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--':
            return False
        if arg in value_flags:
            i += 2
            continue
        if arg.startswith('--jq=') or (arg.startswith('-q') and arg != '-q'):
            i += 1
            continue
        if arg == '--allow-escape-sequences':
            return True
        i += 1
    return False


def _check_gh_log_commands(source):
    """Inspect commands, without mistaking comments/echo strings for calls.

    This is a limited shell lexer (not a complete Bash/YAML interpreter).
    Results remain advisory and are never authorization to write to GitHub.
    """
    source, substitutions = _mask_command_substitutions(source)
    for command in substitutions:
        _check_gh_log_commands(command)
    segments = []
    part = []
    quote = None
    escaped = False
    comment = False
    word_boundary = True

    def flush():
        if part:
            segments.append(''.join(part))
            part.clear()

    for ch in source:
        if comment:
            if ch == '\n':
                flush()
                comment = False
                word_boundary = True
            continue
        if escaped:
            # Backslash-newline is a shell continuation, not a command break.
            if ch != '\n':
                part.extend(('\\', ch))
            escaped = False
            word_boundary = False
        elif ch == '\\' and quote != "'":
            escaped = True
        elif quote:
            part.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            part.append(ch)
            word_boundary = False
        elif ch == '#' and word_boundary:
            comment = True
        elif ch in ';\n&|()':
            flush()
            word_boundary = True
        else:
            part.append(ch)
            word_boundary = ch.isspace()
    require(not quote and not escaped, 'UNPARSEABLE_WORKFLOW_SHELL')
    flush()
    prefixes = {'run:', '-', 'if', 'elif', 'while', 'until', 'then', 'do',
                '!', 'time', 'env', 'command', 'exec', 'sudo'}
    for segment in segments:
        try:
            words = shlex.split(segment, posix=True, comments=False)
        except ValueError as exc:
            raise Blocked('UNPARSEABLE_WORKFLOW_SHELL') from exc
        for i in range(len(words) - 1):
            if words[i:i + 2] != ['gh', 'api']:
                continue
            before = words[:i]
            # Printed text from `echo gh api ...` is not a CLI invocation.
            if not all(word in prefixes or re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*=.*', word)
                       for word in before):
                continue
            args = words[i + 2:]
            if any('/logs' in arg for arg in args) and \
                    not _gh_log_flag_active(args):
                raise Blocked('KNOWN_FAILURE_UNESCAPED_GH_LOG')

def prewrite_review(ledger, intent, proposed_content):
    """Assess a draft before GitHub write; does NOT authenticate owner approval.

    Caller must fetch the head, plan, and owner evidence through an authenticated
    read path, and call this on the same immutable proposed bytes it will write.
    The resulting digest must be matched at the actual write boundary.
    """
    validate_ledger(ledger)
    require(type(intent) is dict and type(proposed_content) is str,
            'INVALID_WRITE_INTENT')
    path = _safe_repo_path(intent.get('path'))
    allowed = intent.get('approved_paths')
    require(type(allowed) is list and bool(allowed) and
            all(type(v) is str and bool(v) for v in allowed) and
            path in allowed, 'PATH_OUTSIDE_APPROVED_SCOPE')
    require(intent.get('operation') in ('create', 'update'), 'INVALID_OPERATION')
    basis = intent.get('fixed_main_head')
    current = intent.get('observed_main_head')
    require(type(basis) is str and bool(SHA40.fullmatch(basis)) and current == basis,
            'MAIN_HEAD_MISMATCH')
    digest = hashlib.sha256(proposed_content.encode('utf-8')).hexdigest()
    require(intent.get('candidate_sha256') == digest, 'CANDIDATE_BYTES_CHANGED')
    # Deterministic checks for observed past code-pattern mistakes.
    if path.startswith('.github/workflows/'):
        _check_gh_log_commands(proposed_content)
        if ('certificate SHA-256 digest:' in proposed_content and
                'Signer #' in proposed_content):
            raise Blocked('KNOWN_FAILURE_WRONG_APKSIGNER_FORMAT')

    # New records remain available as knowledge; do not pretend their
    # free-form prose has automatically become a machine-enforced detector.
    relevant = []
    unresolved = []
    for record in ledger['failures']:
        paths = record['affected_paths']
        if path in paths or '*' in paths:
            relevant.append(record['id'])
            if record['id'] not in EXPECTED or record['status'] == 'OPEN':
                unresolved.append(record['id'])
    return {
        'status': ('CANDIDATE_NEEDS_PREVENTION_REVIEW' if unresolved else
                   'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION'),
        'file_path': path,
        'candidate_sha256': digest,
        'related_failure_ids': relevant,
        'unresolved_failure_ids': unresolved,
        'owner_approval_authenticated_here': False,
        'github_write_performed': False,
    }

def learn_failure(ledger, failure):
    """Propose updated ledger in memory; never commit or push automatically."""
    validate_ledger(ledger)
    require(type(failure) is dict, 'INVALID_NEW_FAILURE')
    # Validate the evidence before the recurrence shortcut; incomplete
    # records must not be accepted merely because their cause_key matches.
    _validate_failure_record(failure)
    require(type(failure['id']) is str and
            bool(re.fullmatch(r'[a-z][a-z0-9_]{2,79}', failure['id'])),
            'BAD_NEW_FAILURE_ID')
    require(failure['status'] == 'OPEN', 'NEW_FAILURE_MUST_BE_OPEN')
    key = failure.get('cause_key')
    require(type(key) is str and bool(re.fullmatch(r'[a-z][a-z0-9_]{2,79}', key)),
            'MISSING_STABLE_CAUSE_KEY')
    for existing in ledger['failures']:
        if existing.get('cause_key', existing['id']) == key:
            return {'action': 'RECURRING_CAUSE_REVIEW_LEARNING_MECHANISM',
                    'existing_id': existing['id'], 'ledger': copy.deepcopy(ledger)}
    require(failure['id'] not in [x['id'] for x in ledger['failures']],
            'DUPLICATE_FAILURE_ID')
    candidate = copy.deepcopy(ledger)
    candidate['failures'].append(copy.deepcopy(failure))
    validate_ledger(candidate)
    return {'action': 'NEW_FAILURE_PROPOSED_NOT_COMMITTED', 'ledger': candidate}

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
    parser.add_argument('--mode', choices=('evaluate', 'prewrite', 'learn'),
                        default='evaluate')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--intent', type=Path)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--failure', type=Path)
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding='utf-8'))
        if args.mode == 'evaluate':
            require(args.evidence is not None, 'MISSING_EVIDENCE_FILE')
            evidence = json.loads(args.evidence.read_text(encoding='utf-8'))
            print(evaluate(ledger, evidence))
        elif args.mode == 'prewrite':
            require(args.intent is not None and args.candidate is not None,
                    'MISSING_INTENT_OR_DRAFT')
            intent = json.loads(args.intent.read_text(encoding='utf-8'))
            proposed = args.candidate.read_text(encoding='utf-8')
            report = prewrite_review(ledger, intent, proposed)
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            if report['status'] != 'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION':
                return 2
        else:
            require(args.failure is not None, 'MISSING_FAILURE_RECORD')
            record = json.loads(args.failure.read_text(encoding='utf-8'))
            print(json.dumps(learn_failure(ledger, record),
                             ensure_ascii=False, sort_keys=True))
    except (Blocked, OSError, ValueError, TypeError) as exc:
        print('BLOCK: ' + str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
