#!/usr/bin/env python3
"""Only new failure-learning candidate tests; does not rerun pre-existing PASS suites."""
import copy
import json
import hashlib
import unittest
from pathlib import Path
from preflight import Blocked, evaluate, prewrite_review, learn_failure, validate_ledger

LEDGER = json.loads(Path(__file__).with_name('failures_v1.json').read_text(encoding='utf-8'))
SHA = 'f087379c5ce646e65f0cec5e23083bf9d28cc787'
OTHER = '4cc03f8b45cb4d4b9cceb82954d1e49949cec443'
CERT = '0cccc7c349bcc0005f53aa1a58f42b1c8ec6a387513f7c33576390842eac301a'
SIGNED = ('Verifies\nVerified using v2 scheme (APK Signature Scheme v2): true\n'
          'Number of signers: 1\nV2 Signer: certificate SHA-256 digest: ' + CERT + '\n')

GOOD = {
    'pr_creation': dict(phase='pr_creation', owner_login='kan1975-creator',
        approval_author_login='kan1975-creator', approval_comment_id=6217557109,
        plan_sha256='a'*64, plan_basis_head=SHA, pr_base_sha=SHA,
        plan_committed_at='2026-10-16T14:21:06Z',
        approval_created_at='2026-10-16T14:22:05Z',
        approval_updated_at='2026-10-16T14:22:05Z',
        pr_created_at='2026-10-16T14:23:30Z',
        plan_path_in_pr=True, approval_ref_in_pr=True),
    'workflow_dispatch': dict(phase='workflow_dispatch',
        gh_api_log_command='gh api --allow-escape-sequences',
        retrieved_log_has_expected_failure=True,
        historical_run_ids=[38839471742,38850603797,38916782780],
        attempt=1,new_run_id=38920000000,history_complete=True),
    'pr_merge': dict(phase='pr_merge',target_pr_head_sha=SHA,
        other_open_pr_heads=[OTHER], all_pr_pages_fetched=True,
        expected_base_sha=OTHER,actual_base_sha=OTHER),
    'apk_signature': dict(phase='apk_signature',apksigner_output=SIGNED),
}

class FailureLearningTest(unittest.TestCase):
    def ok(self, phase):
        self.assertEqual(evaluate(LEDGER, copy.deepcopy(GOOD[phase])),
                         'OFFLINE_PREFLIGHT_PASS_NOT_AUTHORIZATION')
    def blocked(self, phase, **changes):
        data = copy.deepcopy(GOOD[phase])
        data.update(changes)
        with self.assertRaises(Blocked):
            evaluate(LEDGER, data)
    def test_all_four_known_good(self):
        for phase in GOOD:
            with self.subTest(phase=phase):
                self.ok(phase)
    def test_missing_approval(self):
        self.blocked('pr_creation', approval_comment_id=None)
    def test_post_pr_or_post_plan_approval(self):
        self.blocked('pr_creation', approval_created_at='2026-10-16T14:24:00Z')
        self.blocked('pr_creation', approval_created_at='2026-10-16T14:20:00Z')
    def test_mismatched_plan_or_edited_approval(self):
        self.blocked('pr_creation',plan_basis_head=OTHER)
        self.blocked('pr_creation',approval_updated_at='2026-10-16T14:22:06Z')
    def test_missing_pr_approval_ref(self):
        self.blocked('pr_creation',approval_ref_in_pr=False)
    def test_unescaped_gh_log(self):
        self.blocked('workflow_dispatch',gh_api_log_command='gh api')
    def test_log_and_dispatch_history(self):
        self.blocked('workflow_dispatch',retrieved_log_has_expected_failure=False)
        self.blocked('workflow_dispatch',history_complete=False)
        self.blocked('workflow_dispatch',attempt=2)
        self.blocked('workflow_dispatch',new_run_id=38839471742)
    def test_other_open_pr_same_head(self):
        self.blocked('pr_merge',other_open_pr_heads=[SHA])
    def test_merge_snapshot_incomplete_or_stale(self):
        self.blocked('pr_merge',all_pr_pages_fetched=False)
        self.blocked('pr_merge',expected_base_sha=SHA)
    def test_wrong_certificate(self):
        self.blocked('apk_signature',apksigner_output=SIGNED.replace(CERT,'f'+CERT[1:]))
    def test_bad_count_and_bad_v2(self):
        self.blocked('apk_signature',apksigner_output=SIGNED.replace('signers: 1','signers: 2'))
        self.blocked('apk_signature',apksigner_output=SIGNED.replace('v2): true','v2): false'))
    def test_missing_or_duplicate_cert(self):
        row='V2 Signer: certificate SHA-256 digest: '+CERT+'\n'
        self.blocked('apk_signature',apksigner_output=SIGNED.replace(row,''))
        self.blocked('apk_signature',apksigner_output=SIGNED+row)
    def test_malformed_signature_output(self):
        self.blocked('apk_signature',apksigner_output=SIGNED.replace('V2 Signer:','Signer #1'))
    def test_unknown_phase(self):
        with self.assertRaises(Blocked):
            evaluate(LEDGER,dict(phase='unknown'))
    def test_missing_registry_record(self):
        short = copy.deepcopy(LEDGER)
        short['failures']=short['failures'][:-1]
        with self.assertRaises(Blocked):
            evaluate(short,GOOD['apk_signature'])
    def test_duplicate_registry_record(self):
        dup = copy.deepcopy(LEDGER)
        dup['failures'].append(copy.deepcopy(dup['failures'][0]))
        with self.assertRaises(Blocked):
            evaluate(dup,GOOD['pr_creation'])
    def test_new_failure_can_be_recorded_without_weakening_existing_phase(self):
        unknown=copy.deepcopy(LEDGER)
        new=copy.deepcopy(unknown['failures'][0])
        new['id']='unimplemented_future_failure'
        unknown['failures'].append(new)
        validate_ledger(unknown)
        self.assertEqual(evaluate(unknown,GOOD['pr_creation']),
                         'OFFLINE_PREFLIGHT_PASS_NOT_AUTHORIZATION')

class NewPrewriteLearningTests(unittest.TestCase):
    """ONLY added test methods for pre-write learning; run this class in isolation."""
    PATH = '.github/workflows/cb6_signal_one_shot_apk.yml'
    BASE = '4cc03f8b45cb4d4b9cceb82954d1e49949cec443'
    SAFE = ('gh api --allow-escape-sequences "repos/$GITHUB_REPOSITORY/actions/jobs/123/logs"\n'
            "re.findall(r'^V2 Signer: certificate SHA-256 digest: ([0-9a-fA-F]{64})$', text)\n")

    def intent(self, text, **override):
        info = dict(path=self.PATH, approved_paths=[self.PATH],
                    operation='create', fixed_main_head=self.BASE,
                    observed_main_head=self.BASE,
                    candidate_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
        info.update(override)
        return info

    def test_safe_draft_returns_digest_not_authorization(self):
        out = prewrite_review(LEDGER, self.intent(self.SAFE), self.SAFE)
        self.assertEqual(out['status'], 'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION')
        self.assertFalse(out['github_write_performed'])
        self.assertFalse(out['owner_approval_authenticated_here'])

    def test_unescaped_gh_log_rejected_before_write(self):
        broken = self.SAFE.replace('gh api --allow-escape-sequences', 'gh api')
        with self.assertRaisesRegex(Blocked, 'UNESCAPED_GH_LOG'):
            prewrite_review(LEDGER, self.intent(broken), broken)

    def test_old_signer_output_rejected_before_write(self):
        broken = self.SAFE.replace('V2 Signer:', 'Signer #1')
        with self.assertRaisesRegex(Blocked, 'WRONG_APKSIGNER_FORMAT'):
            prewrite_review(LEDGER, self.intent(broken), broken)

    def test_bad_head_scope_digest_rejected(self):
        for override in ({'observed_main_head': 'f'*40},
                         {'approved_paths': ['some_other_path.py']},
                         {'candidate_sha256': '0'*64},
                         {'path': '../outside'}):
            with self.subTest(override=override), self.assertRaises(Blocked):
                prewrite_review(LEDGER, self.intent(self.SAFE, **override), self.SAFE)

    def make_new_failure(self):
        return dict(id='new_failure_from_postcheck', cause_key='new_failure_from_postcheck',
                    phase='file_prepare', root_cause='A new observed failure',
                    evidence=['new job with observed failure'],
                    affected_paths=[self.PATH],
                    prevention='Do not repeat the failure',
                    regression_cases=['valid passes', 'invalid rejected'],
                    status='OPEN')

    def test_new_failure_proposed_and_used_next_time(self):
        result = learn_failure(LEDGER, self.make_new_failure())
        self.assertEqual(result['action'], 'NEW_FAILURE_PROPOSED_NOT_COMMITTED')
        self.assertEqual(len(result['ledger']['failures']), len(LEDGER['failures'])+1)
        self.assertEqual(prewrite_review(result['ledger'], self.intent(self.SAFE), self.SAFE)
                         ['status'], 'CANDIDATE_NEEDS_PREVENTION_REVIEW')

    def test_same_cause_is_mechanism_regression_not_duplicate(self):
        result = learn_failure(LEDGER, self.make_new_failure())
        duplicate = learn_failure(result['ledger'], self.make_new_failure())
        self.assertEqual(duplicate['action'], 'RECURRING_CAUSE_REVIEW_LEARNING_MECHANISM')
        self.assertEqual(len(duplicate['ledger']['failures']), len(result['ledger']['failures']))

    def test_invalid_failure_record_cannot_be_proposed(self):
        wrong = self.make_new_failure()
        wrong.pop('prevention')
        with self.assertRaises(Blocked):
            learn_failure(LEDGER, wrong)

if __name__ == '__main__':
    unittest.main()
