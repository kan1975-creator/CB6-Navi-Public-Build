#!/usr/bin/env python3
"""New-only tests for owner-gated pending failure capture; mocked APIs only."""
import copy
import unittest
from unittest import mock
import auto_failure_ingest as m

RUN = 38954933139
ATTEMPT = 1
ISSUE = 101
APPROVAL = 222
JOB = 555
SHA = 'a' * 40
ROOT = 'repos/' + m.REPO + '/'


class FakeAPI:
    def __init__(self):
        self.posts = []
        self.comments = []
        self.jobs = [{'id': JOB, 'run_id': RUN, 'run_attempt': ATTEMPT,
                      'status': 'completed', 'conclusion': 'failure'}]
        self.data = {
            ROOT + 'branches/main': {'protected': True},
            ROOT + 'branches/cb6-v2-clean': {'protected': True},
            ROOT + 'rulesets/24792110': {
                'enforcement': 'active', 'target': 'branch',
                'bypass_actors': [], 'current_user_can_bypass': 'never',
                'conditions': {'ref_name': {'include': [
                    'refs/heads/main', 'refs/heads/cb6-v2-clean'], 'exclude': []}},
                'rules': [{'type': 'deletion'}, {'type': 'non_fast_forward'},
                          {'type': 'pull_request', 'parameters': {
                              'required_approving_review_count': 0,
                              'require_extra_approval_for_unattributed_changes': True,
                              'allowed_merge_methods': ['merge', 'squash']}},
                          {'type': 'required_status_checks', 'parameters': {
                              'strict_required_status_checks_policy': False,
                              'do_not_enforce_on_create': False,
                              'required_status_checks': [{
                                  'context': m.CHECK, 'integration_id': m.APP_ID}]}}]},
            ROOT + 'issues/101': {
                'number': 101, 'state': 'open', 'user': {'id': m.OWNER_ID}},
            ROOT + 'issues/comments/222': {
                'id': 222,
                'user': {'login': m.OWNER, 'id': m.OWNER_ID},
                'created_at': '2026-10-17T00:00:00Z',
                'updated_at': '2026-10-17T00:00:00Z',
                'issue_url': 'https://api.github.com/repos/' + m.REPO + '/issues/11',
                'body': f'CB6-CAPTURE-ACTIVATE {m.PLAN_SHA} 101'},
            ROOT + f'actions/runs/{RUN}': {
                'id': RUN, 'run_attempt': 1,
                'workflow_id': m.TRUSTED_WORKFLOW_ID,
                'name': m.TRUSTED_WORKFLOW_NAME,
                'event': 'pull_request_target',
                'status': 'completed', 'conclusion': 'failure',
                'repository': {'full_name': m.REPO},
                'head_repository': {'full_name': m.REPO},
                'head_sha': SHA},
        }

    def get(self, path):
        if path.startswith(ROOT + f'actions/runs/{RUN}/jobs?'):
            return copy.deepcopy(self.jobs)
        if path.startswith(ROOT + f'issues/{ISSUE}/comments?'):
            return copy.deepcopy(self.comments)
        return copy.deepcopy(self.data[path])

    def post(self, path, body):
        self.posts.append((path, body))
        self.data[ROOT + 'issues/comments/777'] = {'id': 777, 'body': body['body']}
        self.comments.append({'id': 777, 'body': body['body']})
        return {'id': 777}


class NewPendingCaptureTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()

    def call(self):
        return m.capture(self.api, run_id=RUN, attempt=ATTEMPT,
                         issue_id=ISSUE, approval_comment_id=APPROVAL)

    def block(self):
        with self.assertRaises(m.Blocked):
            self.call()
        self.assertEqual(self.api.posts, [])

    def test_01_verified_persist_once(self):
        result = self.call()
        self.assertEqual(result['status'], 'PENDING_RECORD_PERSISTED_NOT_ADOPTED')
        self.assertEqual(len(self.api.posts), 1)
        self.assertIn('CB6-ROOT-CAUSE UNVERIFIED', self.api.posts[0][1]['body'])

    def test_02_duplicate_not_reposted(self):
        self.call()
        self.assertEqual(self.call()['status'], 'ALREADY_RECORDED_NOT_REPOSTED')
        self.assertEqual(len(self.api.posts), 1)

    def test_03_success_run_not_recorded(self):
        self.api.data[ROOT + f'actions/runs/{RUN}']['conclusion'] = 'success'
        self.block()

    def test_04_untrusted_event_rejected(self):
        self.api.data[ROOT + f'actions/runs/{RUN}']['event'] = 'pull_request'
        self.block()

    def test_05_wrong_workflow_rejected(self):
        self.api.data[ROOT + f'actions/runs/{RUN}']['workflow_id'] = 1
        self.block()

    def test_06_other_repo_rejected(self):
        self.api.data[ROOT + f'actions/runs/{RUN}']['repository']['full_name'] = 'bad/repo'
        self.block()

    def test_07_wrong_attempt_rejected(self):
        self.api.data[ROOT + f'actions/runs/{RUN}']['run_attempt'] = 2
        self.block()

    def test_08_no_failed_job_rejected(self):
        self.api.jobs = []
        self.block()

    def test_09_job_wrong_attempt_rejected(self):
        self.api.jobs[0]['run_attempt'] = 2
        self.block()

    def test_10_edited_activation_rejected(self):
        self.api.data[ROOT + 'issues/comments/222']['updated_at'] = 'later'
        self.block()

    def test_11_wrong_approval_actor_rejected(self):
        self.api.data[ROOT + 'issues/comments/222']['user']['id'] = 1
        self.block()

    def test_12_unapproved_destination_rejected(self):
        self.api.data[ROOT + 'issues/101']['user']['id'] = 1
        self.block()

    def test_13_changed_approval_digest_rejected(self):
        self.api.data[ROOT + 'issues/comments/222']['body'] = 'invalid'
        self.block()

    def test_14_inactive_ruleset_rejected(self):
        self.api.data[ROOT + 'rulesets/24792110']['enforcement'] = 'disabled'
        self.block()

    def test_15_truncated_pagination_rejected(self):
        self.api.comments = [{'body': 'x'}] * 3000
        self.block()

    def test_16_unknown_comment_shape_rejected(self):
        self.api.comments = [None]
        self.block()

    def test_17_unknown_post_result_no_retry(self):
        self.api.post = mock.Mock(return_value={})
        with self.assertRaises(m.Blocked):
            self.call()
        self.assertEqual(self.api.post.call_count, 1)

    def test_18_untrusted_names_never_copied(self):
        self.api.data[ROOT + f'actions/runs/{RUN}']['display_title'] = 'ghp_untrusted'
        self.api.jobs[0]['name'] = 'Bearer secret'
        self.call()
        body = self.api.posts[0][1]['body']
        self.assertNotIn('ghp_', body)
        self.assertNotIn('Bearer secret', body)

    def test_19_invalid_identifier_rejected(self):
        for value in ('0', '-1', 'foo', '1.1', ' 1'):
            with self.assertRaises(m.Blocked):
                m.numeric(value)

    def test_20_incomplete_job_rejected(self):
        self.api.jobs[0]['status'] = 'in_progress'
        self.block()

    def test_21_invalid_run_head_rejected(self):
        self.api.data[ROOT + f'actions/runs/{RUN}']['head_sha'] = 'invalid'
        self.block()


    def test_22_missing_exclude_is_blocked(self):
        del self.api.data[ROOT + 'rulesets/24792110']['conditions']['ref_name']['exclude']
        self.block()

    def test_23_nonempty_exclude_is_blocked(self):
        self.api.data[ROOT + 'rulesets/24792110']['conditions']['ref_name']['exclude'] = ['refs/heads/main']
        self.block()

    def test_24_wrong_required_check_name_is_blocked(self):
        entry = self.api.data[ROOT + 'rulesets/24792110']['rules'][3]
        entry['parameters']['required_status_checks'][0]['context'] = 'wrong'
        self.block()

    def test_25_wrong_required_check_app_is_blocked(self):
        entry = self.api.data[ROOT + 'rulesets/24792110']['rules'][3]
        entry['parameters']['required_status_checks'][0]['integration_id'] = 1
        self.block()

    def test_26_missing_required_check_parameters_is_blocked(self):
        del self.api.data[ROOT + 'rulesets/24792110']['rules'][3]['parameters']
        self.block()

    def test_27_missing_pr_protection_parameters_is_blocked(self):
        del self.api.data[ROOT + 'rulesets/24792110']['rules'][2]['parameters']
        self.block()

    def test_28_pr_protection_weakened_is_blocked(self):
        self.api.data[ROOT + 'rulesets/24792110']['rules'][2]['parameters'][
            'require_extra_approval_for_unattributed_changes'] = False
        self.block()

    def test_29_unprotected_clean_branch_is_blocked(self):
        self.api.data[ROOT + 'branches/cb6-v2-clean']['protected'] = False
        self.block()

    def test_30_bypass_status_missing_is_blocked(self):
        del self.api.data[ROOT + 'rulesets/24792110']['current_user_can_bypass']
        self.block()

    def test_31_status_check_creation_exemption_is_blocked(self):
        self.api.data[ROOT + 'rulesets/24792110']['rules'][3]['parameters'][
            'do_not_enforce_on_create'] = True
        self.block()


    def test_32_missing_ruleset_conditions_is_blocked(self):
        del self.api.data[ROOT + 'rulesets/24792110']['conditions']
        self.block()

    def test_33_duplicate_trusted_check_context_is_blocked(self):
        params = self.api.data[ROOT + 'rulesets/24792110']['rules'][3]['parameters']
        params['required_status_checks'].append({'context': m.CHECK,
                                                  'integration_id': 1})
        self.block()

if __name__ == '__main__':
    unittest.main()
