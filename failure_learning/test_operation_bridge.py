#!/usr/bin/env python3
"""New bridge behavior only; do not rerun existing PASS tests."""
import base64
import copy
import hashlib
import importlib
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Only the new bridge tests run. Its existing preflight dependency is used
# directly, without executing any of the previous PASS test suites.
from preflight import Blocked
import operation_bridge as target

HEAD = '0b77b50a9e752ade56e13865a24456b83d88d47d'
MAIN = '4cc03f8b45cb4d4b9cceb82954d1e49949cec443'
BRANCH = 'feature/cb6-failure-learning-20261017'
PATH = 'failure_learning/new_candidate.txt'
TEXT = 'approved candidate content\n'


def plan(**changes):
    p = dict(repository=target.REPO, pr_number=18, branch=BRANCH,
             expected_head=HEAD, fixed_main_head=MAIN,
             path=PATH, operation='create', approved_paths=[PATH],
             candidate_sha256=hashlib.sha256(TEXT.encode()).hexdigest(),
             approval_comment_id=6221609820, owner_login=target.OWNER,
             owner_id=target.OWNER_ID)
    p.update(changes)
    return p


def as_content(s):
    return {'content': base64.b64encode(s.encode()).decode('ascii'),
            'encoding': 'base64', 'sha': 'a'*40}


class FakeGH:
    def __init__(self, p):
        self.plan = p
        self.writes = []
        self.read_count = 0
        self.existing = None
        self.ledger = json.loads(Path(__file__).with_name('failures_v1.json').read_text(encoding='utf-8'))
        self.tamper = {}

    def get(self, url):
        self.read_count += 1
        root = 'repos/' + target.REPO + '/'
        values = {
            'user': {'login': target.OWNER, 'id': target.OWNER_ID},
            root + 'branches/main': {'commit': {'sha': MAIN}, 'protected': True},
            root + 'branches/' + BRANCH: {'commit': {'sha': HEAD}},
            root + 'pulls/18': {'state': 'open', 'merged_at': None,
                                'head': {'sha': HEAD, 'ref': BRANCH},
                                'base': {'sha': MAIN}},
            root + 'rulesets/24792110': {
                'enforcement': 'active', 'bypass_actors': [],
                'conditions': {'ref_name': {'include': ['refs/heads/main',
                                                       'refs/heads/cb6-v2-clean']}},
                'rules': [{'type': 'required_status_checks', 'parameters': {
                    'required_status_checks': [{'context': target.CHECK,
                                                'integration_id': target.APP_ID}]}}]},
            root + 'issues/comments/6221609820': {
                'user': {'login': target.OWNER, 'id': target.OWNER_ID},
                'issue_url': 'https://api.github.com/' + root + 'issues/11',
                'created_at': '2026-10-17T00:00:00Z',
                'updated_at': '2026-10-17T00:00:00Z',
                'body': target.plan_binding(self.plan)},
            root + 'contents/failure_learning/failures_v1.json?ref=' + HEAD:
                as_content(json.dumps(self.ledger)),
        }
        path = root + 'contents/' + self.plan['path']
        if url.startswith(path + '?ref='):
            if url.endswith('?ref=' + self.plan['expected_head']):
                return as_content(TEXT)
            return as_content(TEXT)
        result = values.get(url)
        if url in self.tamper:
            return self.tamper[url]
        if result is None:
            raise AssertionError('UNEXPECTED_READ: '+url)
        return result

    def get_optional(self, url):
        return self.existing

    def put(self, url, data):
        self.writes.append((url, data))
        return {'commit': {'sha': 'd'*40}}


def new_failure(**changes):
    record = dict(id='new_bridge_failure', cause_key='new_bridge_failure',
                  phase='file_prepare', root_cause='New observed failure',
                  evidence=['New observed log'], affected_paths=[PATH],
                  prevention='Prevent this on the next operation',
                  regression_cases=['allowed case accepted', 'invalid case blocked'],
                  status='OPEN')
    record.update(changes)
    return record


class BridgeOnlyNewTests(unittest.TestCase):
    def test_new_create_only_after_verified_comment_and_head(self):
        p = plan()
        gh = FakeGH(p)
        report = target.apply_approved_write(gh, p, TEXT)
        self.assertEqual(report['status'], 'WRITE_COMPLETE_NOT_MERGED')
        self.assertEqual(len(gh.writes), 1)
        self.assertEqual(base64.b64decode(gh.writes[0][1]['content']).decode(), TEXT)
        self.assertEqual(gh.writes[0][1]['branch'], BRANCH)

    def test_wrong_digest_blocked_before_api_access(self):
        p = plan(candidate_sha256='0'*64)
        gh = FakeGH(p)
        with self.assertRaisesRegex(Blocked, 'CANDIDATE_DIGEST_MISMATCH'):
            target.apply_approved_write(gh, p, TEXT)
        self.assertEqual(gh.read_count, 0)
        self.assertEqual(gh.writes, [])

    def test_frozen_paths_never_accepted(self):
        for frozen in ('v2/core/sig.py', '.github/workflows/abc.yml',
                       'PUBLIC_BUILD_NOTICE.md', '../outside', '/root/file'):
            with self.subTest(path=frozen):
                p = plan(path=frozen, approved_paths=[frozen])
                with self.assertRaises(Blocked):
                    target.apply_approved_write(FakeGH(p), p, TEXT)

    def test_new_path_outside_approval_blocked(self):
        p = plan(path='failure_learning/other.txt')
        with self.assertRaisesRegex(Blocked, 'OPERATION_NOT_APPROVED'):
            target.apply_approved_write(FakeGH(p), p, TEXT)

    def test_unsafe_api_path_characters_rejected(self):
        for value in ('failure_learning/file?ref=main',
                      'failure_learning/file\nname', 'failure_learning/file#tag'):
            p = plan(path=value, approved_paths=[value])
            with self.subTest(path=value), self.assertRaises(Blocked):
                target.apply_approved_write(FakeGH(p), p, TEXT)

    def test_owner_identity_mismatch_blocks(self):
        p = plan()
        gh = FakeGH(p)
        gh.tamper['user'] = {'login': 'attacker', 'id': 10}
        with self.assertRaisesRegex(Blocked, 'WRONG_AUTHENTICATED_ACTOR'):
            target.apply_approved_write(gh, p, TEXT)
        self.assertFalse(gh.writes)

    def test_unapproved_or_edited_comment_blocks(self):
        p = plan()
        for change in ({'body': 'NOT_APPROVED'},
                       {'updated_at': '2026-10-18T00:00:00Z'},
                       {'issue_url': 'https://api.github.com/repos/'+target.REPO+'/issues/18'}):
            with self.subTest(change=change):
                gh = FakeGH(p)
                root = 'repos/' + target.REPO + '/'
                c = gh.get(root+'issues/comments/6221609820').copy()
                c.update(change)
                gh.tamper[root+'issues/comments/6221609820'] = c
                with self.assertRaisesRegex(Blocked, 'OWNER_APPROVAL_UNVERIFIED'):
                    target.apply_approved_write(gh, p, TEXT)
                self.assertFalse(gh.writes)

    def test_wrong_main_pr_and_branch_block(self):
        p = plan()
        root = 'repos/' + target.REPO + '/'
        for key, value in [
            (root + 'branches/main', {'commit': {'sha': 'e'*40}, 'protected': True}),
            (root + 'branches/' + BRANCH, {'commit': {'sha': 'f'*40}}),
            (root + 'pulls/18', {'state': 'closed', 'merged_at': None})]:
            with self.subTest(key=key):
                gh = FakeGH(p)
                gh.tamper[key] = value
                with self.assertRaises(Blocked):
                    target.apply_approved_write(gh, p, TEXT)
                self.assertFalse(gh.writes)

    def test_missing_protected_branch_scope_blocks(self):
        p = plan()
        gh = FakeGH(p)
        root = 'repos/' + target.REPO + '/'
        rules = copy.deepcopy(gh.get(root + 'rulesets/24792110'))
        rules['conditions']['ref_name']['include'] = ['refs/heads/main']
        gh.tamper[root + 'rulesets/24792110'] = rules
        with self.assertRaisesRegex(Blocked, 'RULESET_INACTIVE_OR_BYPASS'):
            target.apply_approved_write(gh, p, TEXT)
        self.assertFalse(gh.writes)

    def test_missing_ruleset_protection_blocks(self):
        p = plan()
        gh = FakeGH(p)
        root = 'repos/' + target.REPO + '/'
        r = gh.get(root+'rulesets/24792110').copy()
        r['bypass_actors'] = [{'actor_id': 1}]
        gh.tamper[root+'rulesets/24792110'] = r
        with self.assertRaisesRegex(Blocked, 'RULESET_INACTIVE_OR_BYPASS'):
            target.apply_approved_write(gh, p, TEXT)
        self.assertFalse(gh.writes)

    def test_existing_file_prevents_create(self):
        p = plan()
        gh = FakeGH(p)
        gh.existing = as_content('already present')
        with self.assertRaisesRegex(Blocked, 'FILE_ALREADY_EXISTS'):
            target.apply_approved_write(gh, p, TEXT)
        self.assertFalse(gh.writes)

    def test_update_requires_exact_content_blob(self):
        p = plan(operation='update')
        gh = FakeGH(p)
        with self.assertRaisesRegex(Blocked, 'MISSING_UPDATE_BLOB_SHA'):
            target.apply_approved_write(gh, p, TEXT)
        gh.existing = as_content('old')
        report = target.apply_approved_write(gh, p, TEXT)
        self.assertEqual(report['commit_sha'], 'd'*40)
        self.assertEqual(gh.writes[0][1]['sha'], 'a'*40)

    def test_unresolved_prewrite_blocks_before_put(self):
        p = plan()
        gh = FakeGH(p)
        with patch.object(target, 'prewrite_review', return_value={
            'status': 'CANDIDATE_NEEDS_PREVENTION_REVIEW',
            'candidate_sha256': p['candidate_sha256']}):
            with self.assertRaisesRegex(Blocked, 'PREFLIGHT_UNRESOLVED_OR_MISMATCH'):
                target.apply_approved_write(gh, p, TEXT)
        self.assertFalse(gh.writes)

    def test_postcheck_proposes_new_record_without_writing(self):
        p = plan()
        gh = FakeGH(p)
        ledger = json.loads(Path(__file__).with_name('failures_v1.json').read_text(encoding='utf-8'))
        proposal = target.propose_postcheck(ledger, new_failure())
        self.assertEqual(proposal['action'], 'NEW_FAILURE_PROPOSED_NOT_COMMITTED')
        self.assertEqual(len(proposal['ledger']['failures']), len(ledger['failures']) + 1)
        self.assertEqual(gh.writes, [])

    def test_same_cause_is_a_learning_mechanism_regression(self):
        ledger = json.loads(Path(__file__).with_name('failures_v1.json').read_text(encoding='utf-8'))
        report = target.propose_postcheck(ledger, new_failure(cause_key=ledger['failures'][0].get('cause_key', ledger['failures'][0]['id'])))
        self.assertEqual(report['action'], 'RECURRING_CAUSE_REVIEW_LEARNING_MECHANISM')
        self.assertEqual(len(ledger['failures']), 4)

    def test_import_has_no_automatic_github_writes(self):
        self.assertFalse(hasattr(target, 'AUTO_RUN'))


if __name__ == '__main__':
    unittest.main()
