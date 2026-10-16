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

class FailTwoOnlyRegressionTests(unittest.TestCase):
    """Only new tests for the two independent-review failures."""
    PATH = '.github/workflows/cb6_signal_one_shot_apk.yml'
    BASE = '4cc03f8b45cb4d4b9cceb82954d1e49949cec443'

    def draft(self, content):
        return dict(path=self.PATH, approved_paths=[self.PATH], operation='create',
                    fixed_main_head=self.BASE, observed_main_head=self.BASE,
                    candidate_sha256=hashlib.sha256(content.encode()).hexdigest())

    def assert_blocked(self, content):
        with self.assertRaisesRegex(Blocked, 'UNESCAPED_GH_LOG'):
            prewrite_review(LEDGER, self.draft(content), content)

    def matching_cause(self):
        record = copy.deepcopy(NewPrewriteLearningTests().make_new_failure())
        record['cause_key'] = LEDGER['failures'][0].get('cause_key', LEDGER['failures'][0]['id'])
        return record

    def test_fail1_backslash_multiline_missing_flag_is_blocked(self):
        self.assert_blocked('gh api \\\n    "repos/$GITHUB_REPOSITORY/actions/jobs/123/logs"\n')

    def test_fail1_quoted_multiline_missing_flag_is_blocked(self):
        self.assert_blocked('gh api "repos/$GITHUB_REPOSITORY/actions/jobs/\n123/logs"\n')

    def test_fail1_flag_on_separate_command_does_not_mask_missing_flag(self):
        self.assert_blocked('gh api --allow-escape-sequences repos/x/y\n'
                            'gh api \\\n    "repos/$GITHUB_REPOSITORY/actions/jobs/123/logs"\n')

    def test_fail1_multiline_flag_at_start_is_accepted(self):
        content = ('gh api --allow-escape-sequences \\\n'
                   '    "repos/$GITHUB_REPOSITORY/actions/jobs/123/logs"\n')
        self.assertEqual(prewrite_review(LEDGER, self.draft(content), content)['status'],
                         'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION')

    def test_fail1_multiline_flag_on_continuation_is_accepted(self):
        content = ('gh api \\\n'
                   '    --allow-escape-sequences \\\n'
                   '    "repos/$GITHUB_REPOSITORY/actions/jobs/123/logs"\n')
        self.assertEqual(prewrite_review(LEDGER, self.draft(content), content)['status'],
                         'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION')

    def test_fail2_recurring_missing_evidence_is_blocked(self):
        record = self.matching_cause()
        record.pop('evidence')
        with self.assertRaises(Blocked):
            learn_failure(LEDGER, record)

    def test_fail2_recurring_empty_evidence_is_blocked(self):
        record = self.matching_cause()
        record['evidence'] = []
        with self.assertRaises(Blocked):
            learn_failure(LEDGER, record)

    def test_fail2_recurring_missing_prevention_is_blocked(self):
        record = self.matching_cause()
        record.pop('prevention')
        with self.assertRaises(Blocked):
            learn_failure(LEDGER, record)

    def test_fail2_recurring_invalid_regression_cases_is_blocked(self):
        record = self.matching_cause()
        record['regression_cases'] = ['only one']
        with self.assertRaises(Blocked):
            learn_failure(LEDGER, record)

    def test_fail2_recurring_invalid_status_is_blocked(self):
        record = self.matching_cause()
        record['status'] = 'PREVENTION_VERIFIED'
        with self.assertRaises(Blocked):
            learn_failure(LEDGER, record)

    def test_fail2_recurring_blank_phase_and_evidence_are_blocked(self):
        for field, value in [('phase', '  '), ('evidence', ['  '])]:
            record = self.matching_cause()
            record[field] = value
            with self.subTest(field=field), self.assertRaises(Blocked):
                learn_failure(LEDGER, record)

    def test_fail2_recurring_valid_evidence_returns_review(self):
        record = self.matching_cause()
        result = learn_failure(LEDGER, record)
        self.assertEqual(result['action'], 'RECURRING_CAUSE_REVIEW_LEARNING_MECHANISM')
        self.assertEqual(result['existing_id'], LEDGER['failures'][0]['id'])
        self.assertEqual(result['ledger'], LEDGER)

class IndependentReviewFollowupTests(unittest.TestCase):
    """ONLY tests added for the latest two shell-command review failures."""
    PATH = '.github/workflows/cb6_signal_one_shot_apk.yml'
    BASE = '4cc03f8b45cb4d4b9cceb82954d1e49949cec443'

    def review(self, draft):
        intent = dict(path=self.PATH, approved_paths=[self.PATH],
                      operation='create', fixed_main_head=self.BASE,
                      observed_main_head=self.BASE,
                      candidate_sha256=hashlib.sha256(draft.encode()).hexdigest())
        return prewrite_review(LEDGER, intent, draft)

    def blocked(self, draft):
        with self.assertRaisesRegex(Blocked, 'UNESCAPED_GH_LOG'):
            self.review(draft)

    def accepted(self, draft):
        self.assertEqual(self.review(draft)['status'],
                         'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION')

    def test_separate_semicolon_command_flag_cannot_mask_missing(self):
        self.blocked('gh api repos/x/actions/jobs/1/logs; '
                     'gh api --allow-escape-sequences repos/x\n')

    def test_separate_semicolon_command_flag_before_unsafe(self):
        self.blocked('gh api --allow-escape-sequences repos/x; '
                     'gh api repos/x/actions/jobs/1/logs\n')

    def test_comment_flag_does_not_count(self):
        self.blocked('gh api repos/x/actions/jobs/1/logs # --allow-escape-sequences\n')

    def test_comment_flag_on_previous_line_does_not_count(self):
        self.blocked('# --allow-escape-sequences\n'
                     'gh api repos/x/actions/jobs/1/logs\n')

    def test_separate_line_with_flag_does_not_count(self):
        self.blocked('gh api repos/x/actions/jobs/1/logs\n'
                     'echo --allow-escape-sequences\n')

    def test_backslash_multiline_with_comment_flag_still_blocked(self):
        self.blocked('gh api \\\n    repos/x/actions/jobs/1/logs  # --allow-escape-sequences\n')

    def test_echo_double_quoted_multiline_is_not_command(self):
        self.accepted('echo "gh api\nrepos/x/actions/jobs/1/logs"\n')

    def test_echo_single_quoted_multiline_is_not_command(self):
        self.accepted("echo 'gh api\nrepos/x/actions/jobs/1/logs'\n")

    def test_yaml_run_echo_multiline_is_not_command(self):
        self.accepted('jobs:\n  build:\n    steps:\n'
                      '      - run: |\n'
                      '          echo "gh api\n'
                      '          repos/x/actions/jobs/1/logs"\n')

    def test_echo_unquoted_gh_words_is_not_command(self):
        self.accepted('echo gh api repos/x/actions/jobs/1/logs\n')

    def test_safe_command_after_echo_multiline_is_accepted(self):
        self.accepted('echo "gh api\nrepos/x/actions/jobs/1/logs"; '
                      'gh api --allow-escape-sequences repos/x/actions/jobs/1/logs\n')

    def test_yaml_real_unsafe_gh_command_is_blocked(self):
        self.blocked('jobs:\n  build:\n    steps:\n'
                     '      - run: |\n'
                     '          gh api repos/x/actions/jobs/1/logs\n')

    def test_conditional_gh_command_is_blocked(self):
        self.blocked('if ! gh api repos/x/actions/jobs/1/logs; then echo bad; fi\n')

    def test_quoted_multiline_real_command_still_blocked(self):
        self.blocked('gh api "repos/x/actions/jobs/\n1/logs"\n')

    def test_quoted_hash_followed_by_unsafe_command_is_not_comment(self):
        self.blocked('echo "#"; gh api repos/x/actions/jobs/1/logs\n')

    def test_quoted_semicolon_in_echo_does_not_create_command(self):
        self.accepted("echo '; gh api repos/x/actions/jobs/1/logs'\n")

    def test_embedded_url_hash_does_not_turn_into_comment(self):
        self.blocked('echo repos/x#frag; gh api repos/x/actions/jobs/1/logs\n')

    def test_safe_real_command_with_comment_is_accepted(self):
        self.accepted('gh api --allow-escape-sequences repos/x/actions/jobs/1/logs '
                      '# harmless comment\n')

    def test_safe_real_command_with_backslash_is_accepted(self):
        self.accepted('gh api --allow-escape-sequences \\\n    repos/x/actions/jobs/1/logs\n')

class ReviewResidualSubstitutionAndJqTests(unittest.TestCase):
    """ONLY new FAIL tests: executable substitutions versus literal --jq text."""
    PATH = '.github/workflows/cb6_signal_one_shot_apk.yml'
    BASE = '4cc03f8b45cb4d4b9cceb82954d1e49949cec443'

    def review(self, command):
        intent = dict(path=self.PATH, approved_paths=[self.PATH],
                      operation='create', fixed_main_head=self.BASE,
                      observed_main_head=self.BASE,
                      candidate_sha256=hashlib.sha256(command.encode()).hexdigest())
        return prewrite_review(LEDGER, intent, command)

    def blocked(self, command):
        with self.assertRaisesRegex(Blocked, 'UNESCAPED_GH_LOG'):
            self.review(command)

    def accepted(self, command):
        self.assertEqual(self.review(command)['status'],
                         'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION')

    def test_unescaped_substitution_inside_double_quoted_echo_blocked(self):
        self.blocked('echo "status: $(gh api repos/x/actions/jobs/1/logs)"\n')

    def test_unescaped_substitution_in_double_quoted_assignment_blocked(self):
        self.blocked('answer="$(gh api repos/x/actions/jobs/1/logs)"\n')

    def test_unescaped_substitution_inside_printf_blocked(self):
        self.blocked('printf "%s" "$(gh api repos/x/actions/jobs/1/logs)"\n')

    def test_unescaped_substitution_unquoted_blocked(self):
        self.blocked('answer=$(gh api repos/x/actions/jobs/1/logs)\n')

    def test_unescaped_nested_substitution_blocked(self):
        self.blocked('echo "$(printf "%s" "$(gh api repos/x/actions/jobs/1/logs)")"\n')

    def test_safe_substitution_inside_double_quotes_accepted(self):
        self.accepted('echo "$(gh api --allow-escape-sequences repos/x/actions/jobs/1/logs)"\n')

    def test_literal_substitution_in_single_quotes_not_executed(self):
        self.accepted("echo '$(gh api repos/x/actions/jobs/1/logs)'\n")

    def test_escaped_substitution_in_double_quotes_not_executed(self):
        self.accepted('echo "\\$(gh api repos/x/actions/jobs/1/logs)"\n')

    def test_quoted_echo_gh_words_are_not_invocations(self):
        self.accepted('echo "gh api repos/x/actions/jobs/1/logs"\n')

    def test_flag_only_in_jq_value_does_not_count(self):
        self.blocked('gh api repos/x/actions/jobs/1/logs --jq "--allow-escape-sequences"\n')

    def test_jq_value_before_endpoint_does_not_count(self):
        self.blocked('gh api --jq "--allow-escape-sequences" repos/x/actions/jobs/1/logs\n')

    def test_short_q_value_does_not_count(self):
        self.blocked('gh api repos/x/actions/jobs/1/logs -q "--allow-escape-sequences"\n')

    def test_equals_jq_value_does_not_count(self):
        self.blocked('gh api repos/x/actions/jobs/1/logs --jq=--allow-escape-sequences\n')

    def test_cli_flag_before_jq_value_accepted(self):
        self.accepted('gh api --allow-escape-sequences repos/x/actions/jobs/1/logs --jq .\n')

    def test_cli_flag_after_jq_value_accepted(self):
        self.accepted('gh api repos/x/actions/jobs/1/logs --jq . --allow-escape-sequences\n')

    def test_jq_text_plus_other_unsafe_substitution_blocked(self):
        self.blocked("echo \"$(gh api repos/x/actions/jobs/1/logs --jq '--allow-escape-sequences')\"\n")

    def test_safe_real_gh_with_inert_jq_text_accepted(self):
        self.accepted("echo \"$(gh api --allow-escape-sequences repos/x/actions/jobs/1/logs --jq 'x')\"\n")

class ReviewEscapedNewlineDollarParenTests(unittest.TestCase):
    """ONLY new residual FAIL-1 checks: executable $\\\n( substitution."""
    PATH = '.github/workflows/cb6_signal_one_shot_apk.yml'
    BASE = '4cc03f8b45cb4d4b9cceb82954d1e49949cec443'
    ENDPOINT = 'repos/x/actions/jobs/1/logs'
    CONTINUED_OPEN = '$' + '\\' + '\n' + '('

    def review(self, command):
        intent = dict(path=self.PATH, approved_paths=[self.PATH],
                      operation='create', fixed_main_head=self.BASE,
                      observed_main_head=self.BASE,
                      candidate_sha256=hashlib.sha256(command.encode()).hexdigest())
        return prewrite_review(LEDGER, intent, command)

    def blocked(self, command):
        with self.assertRaisesRegex(Blocked, 'UNESCAPED_GH_LOG'):
            self.review(command)

    def accepted(self, command):
        self.assertEqual(self.review(command)['status'],
                         'CANDIDATE_PREFLIGHT_PASS_NOT_WRITE_AUTHORIZATION')

    def test_line_joined_substitution_inside_double_quotes_blocked(self):
        self.blocked('echo "run: ' + self.CONTINUED_OPEN +
                     'gh api ' + self.ENDPOINT + ')"\n')

    def test_line_joined_substitution_unquoted_blocked(self):
        self.blocked('answer=' + self.CONTINUED_OPEN +
                     'gh api ' + self.ENDPOINT + ')\n')

    def test_line_joined_substitution_in_printf_argument_blocked(self):
        self.blocked('printf "%s" "' + self.CONTINUED_OPEN +
                     'gh api ' + self.ENDPOINT + ')"\n')

    def test_line_joined_substitution_inside_outer_substitution_blocked(self):
        self.blocked('echo "$(printf "%s" "' + self.CONTINUED_OPEN +
                     'gh api ' + self.ENDPOINT + ')")"\n')

    def test_line_joined_substitution_double_continuation_blocked(self):
        twice = '$' + '\\' + '\n' + '\\' + '\n' + '('
        self.blocked('echo "' + twice + 'gh api ' + self.ENDPOINT + ')"\n')

    def test_line_joined_substitution_with_flag_accepted(self):
        self.accepted('echo "' + self.CONTINUED_OPEN +
                      'gh api --allow-escape-sequences ' + self.ENDPOINT + ')"\n')

    def test_line_joined_substitution_with_flag_only_in_jq_value_blocked(self):
        self.blocked('echo "' + self.CONTINUED_OPEN +
                     "gh api " + self.ENDPOINT + " --jq '--allow-escape-sequences')" + '"\n')

    def test_line_joined_substitution_single_quoted_literal_accepted(self):
        self.accepted("echo '" + self.CONTINUED_OPEN +
                      'gh api ' + self.ENDPOINT + ")'\n")

    def test_line_joined_substitution_escaped_dollar_literal_accepted(self):
        literal = '\\' + self.CONTINUED_OPEN
        self.accepted('echo "' + literal + 'gh api ' + self.ENDPOINT + ')"\n')

    def test_comment_does_not_hide_next_line_executable_group(self):
        self.blocked('# ' + self.CONTINUED_OPEN +
                      'gh api ' + self.ENDPOINT + ')\n')

if __name__ == '__main__':
    unittest.main()
