#!/usr/bin/env python3
"""New-only isolated atomic Git ref boundary tests; no GitHub writes."""
import base64
import hashlib
import unittest
from unittest import mock
import operation_bridge as b

HEAD = 'a' * 40
COMMIT = 'c' * 40
BLOB = 'b' * 40
TREE = 'd' * 40
ROOT = 'repos/kan1975-creator/CB6-Navi-Public-Build/'
PATH = 'failure_learning/safe.txt'
CANDIDATE = 'one approved candidate\n'


def plan(operation='create'):
    return {'expected_head': HEAD, 'fixed_main_head': HEAD,
            'branch': 'feature/safe', 'path': PATH, 'operation': operation,
            'approved_paths': [PATH],
            'candidate_sha256': hashlib.sha256(CANDIDATE.encode()).hexdigest()}


class FakeGit:
    def __init__(self, operation='create'):
        self.head = HEAD
        self.reject_guard = False
        self.fail_step = None
        self.post_calls = []
        self.patch_calls = []
        self.value = None if operation == 'create' else {'sha': 'e' * 40}
        self.written = ''

    def get(self, path):
        if path.startswith(ROOT + 'contents/failure_learning/failures_v1.json'):
            return {'encoding': 'base64',
                    'content': base64.b64encode(b'{"schema":1}').decode()}
        if path == ROOT + 'git/commits/' + HEAD:
            return {'tree': {'sha': 'f' * 40}}
        if path.startswith(ROOT + 'branches/'):
            return {'commit': {'sha': self.head}}
        if path.startswith(ROOT + 'contents/' + PATH + '?ref='):
            return {'sha': BLOB, 'encoding': 'base64',
                    'content': base64.b64encode(self.written.encode()).decode()}
        raise AssertionError(path)

    def get_optional(self, path):
        return self.value

    def post(self, path, data):
        self.post_calls.append((path, data))
        if self.fail_step == 'post':
            raise TimeoutError()
        if path == ROOT + 'git/blobs':
            self.written = base64.b64decode(data['content']).decode()
            return {'sha': BLOB}
        if path == ROOT + 'git/trees':
            return {'sha': TREE}
        if path == ROOT + 'git/commits':
            return {'sha': COMMIT, 'parents': [{'sha': HEAD}]}
        raise AssertionError(path)

    def patch(self, path, data):
        self.patch_calls.append((path, data))
        if self.fail_step == 'patch':
            raise TimeoutError()
        if self.fail_step == 'conflict':
            raise b.Blocked('BRANCH_UPDATE_REJECTED')
        self.head = COMMIT
        if self.fail_step == 'ambiguous_result':
            return {}
        return {'object': {'sha': COMMIT}}


class NewAtomicBoundaryTests(unittest.TestCase):
    def setUp(self):
        # Existing identity/approval/RULESET/ledger checks are previously
        # reviewed. Only the new single ref-update boundary is tested.
        def auth(api, candidate_plan):
            if api.reject_guard or api.head != candidate_plan['expected_head']:
                raise b.Blocked('HEAD_OR_AUTH_CHANGED')
            return ROOT

        def check(candidate_plan, candidate):
            if candidate_plan['candidate_sha256'] != hashlib.sha256(
                    candidate.encode()).hexdigest():
                raise b.Blocked('CANDIDATE_DIGEST_MISMATCH')
        replacements = (
            ('authenticated_evidence', auth),
            ('check_plan', check),
            ('validate_ledger', lambda _: None),
            ('prewrite_review', lambda _ledger, intent, _candidate: {
                'status': 'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION',
                'candidate_sha256': intent['candidate_sha256']}))
        for attr, replacement in replacements:
            patcher = mock.patch.object(b, attr, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def block(self, api, candidate_plan):
        with self.assertRaises(b.Blocked):
            b.apply_approved_write(api, candidate_plan, CANDIDATE)

    def test_01_valid_create_nonforce_once(self):
        api = FakeGit()
        result = b.apply_approved_write(api, plan(), CANDIDATE)
        self.assertEqual(result['commit_sha'], COMMIT)
        self.assertEqual(len(api.patch_calls), 1)
        self.assertIs(api.patch_calls[0][1]['force'], False)
        self.assertEqual(api.post_calls[2][1]['parents'], [HEAD])

    def test_02_valid_update(self):
        api = FakeGit('update')
        self.assertEqual(b.apply_approved_write(api, plan('update'), CANDIDATE)
                         ['status'], 'WRITE_COMPLETE_NOT_MERGED')

    def test_03_existing_create_block(self):
        api = FakeGit()
        api.value = {'sha': 'e' * 40}
        self.block(api, plan())
        self.assertEqual(api.patch_calls, [])

    def test_04_missing_update_block(self):
        self.block(FakeGit(), plan('update'))

    def test_05_digest_mismatch_block(self):
        self.block(FakeGit(), {**plan(), 'candidate_sha256': '0' * 64})

    def test_06_guard_denial_block(self):
        api = FakeGit()
        api.reject_guard = True
        self.block(api, plan())

    def test_07_stale_head_block(self):
        api = FakeGit()
        api.head = '9' * 40
        self.block(api, plan())

    def test_08_concurrent_ref_conflict_one_attempt(self):
        api = FakeGit()
        api.fail_step = 'conflict'
        self.block(api, plan())
        self.assertEqual(len(api.patch_calls), 1)

    def test_09_unknown_ref_result_one_attempt(self):
        api = FakeGit()
        api.fail_step = 'ambiguous_result'
        self.block(api, plan())
        self.assertEqual(len(api.patch_calls), 1)

    def test_10_timeout_no_retry(self):
        api = FakeGit()
        api.fail_step = 'patch'
        with self.assertRaises(TimeoutError):
            b.apply_approved_write(api, plan(), CANDIDATE)
        self.assertEqual(len(api.patch_calls), 1)

    def test_11_object_upload_failure_no_ref(self):
        api = FakeGit()
        api.fail_step = 'post'
        with self.assertRaises(TimeoutError):
            b.apply_approved_write(api, plan(), CANDIDATE)
        self.assertEqual(api.patch_calls, [])

    def test_12_missing_parent_tree(self):
        api = FakeGit()
        old_get = api.get
        def get(path):
            return {'tree': {}} if path == ROOT + 'git/commits/' + HEAD else old_get(path)
        api.get = get
        self.block(api, plan())

    def test_13_wrong_new_commit_parent(self):
        api = FakeGit()
        old_post = api.post
        def post(path, obj):
            result = old_post(path, obj)
            if path == ROOT + 'git/commits':
                result['parents'] = [{'sha': '9' * 40}]
            return result
        api.post = post
        self.block(api, plan())

    def test_14_bad_blob_sha(self):
        api = FakeGit()
        old_post = api.post
        def post(path, obj):
            result = old_post(path, obj)
            return {'sha': 'bad'} if path == ROOT + 'git/blobs' else result
        api.post = post
        self.block(api, plan())

    def test_15_wrong_postwrite_bytes(self):
        api = FakeGit()
        old_get = api.get
        def get(path):
            result = old_get(path)
            if path == ROOT + 'contents/' + PATH + '?ref=' + COMMIT:
                result['content'] = base64.b64encode(b'wrong').decode()
            return result
        api.get = get
        self.block(api, plan())
        self.assertEqual(len(api.patch_calls), 1)

    def test_16_wrong_postwrite_branch(self):
        api = FakeGit()
        old_get = api.get
        def get(path):
            if path == ROOT + 'branches/feature/safe' and api.patch_calls:
                return {'commit': {'sha': HEAD}}
            return old_get(path)
        api.get = get
        self.block(api, plan())

    def test_17_no_contents_put(self):
        api = FakeGit()
        b.apply_approved_write(api, plan(), CANDIDATE)
        self.assertEqual([x[0] for x in api.post_calls],
                         [ROOT + 'git/blobs', ROOT + 'git/trees',
                          ROOT + 'git/commits'])

    def test_18_preflight_denial_no_git_objects(self):
        api = FakeGit()
        with mock.patch.object(b, 'prewrite_review',
              return_value={'status': 'BLOCKED',
                            'candidate_sha256': plan()['candidate_sha256']}):
            self.block(api, plan())
        self.assertEqual(api.post_calls, [])


if __name__ == '__main__':
    unittest.main()
