#!/usr/bin/env python3
"""New-only tests for CB6 explicit guarded-operation wiring."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import guarded_operation as g
from preflight import Blocked

HEAD = 'a' * 40
SHA = 'b' * 40


def approved():
    return {'path': 'failure_learning/new.txt', 'operation': 'create',
            'expected_head': HEAD}


def failure(cause_key='fresh_failure', name='fresh_failure'):
    return {'id': name, 'cause_key': cause_key,
            'phase': 'workflow_dispatch', 'root_cause': 'Observed command error',
            'evidence': ['Job #123 failure in step 3'],
            'affected_paths': ['failure_learning/new.txt'],
            'prevention': 'Verify the failing condition before a future write',
            'regression_cases': ['negative rejects', 'positive accepts'],
            'status': 'OPEN'}


def ledger():
    fs = []
    from preflight import EXPECTED
    for id_, phase in EXPECTED.items():
        fs.append({'id': id_, 'phase': phase, 'root_cause': 'Prior verified failure',
                   'evidence': ['owner issue reference'], 'affected_paths': ['*'],
                   'prevention': 'Block repeating known error',
                   'regression_cases': ['positive', 'negative'],
                   'status': 'PREVENTION_PROPOSED'})
    return {'schema': 1, 'candidate_only': True, 'failures': fs}


class OnlyNewWiringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def files(self):
        return sorted(self.dir.glob('cb6_pending_failure_*.json'))

    def test_01_approved_one_call(self):
        writer = mock.Mock(return_value={'status': 'WRITE_COMPLETE_NOT_MERGED',
                          'commit_sha': SHA, 'path': approved()['path'],
                          'candidate_sha256': g.hashlib.sha256(b'draft').hexdigest()})
        result = g.run_approved(None, approved(), 'draft', self.dir, writer=writer)
        self.assertEqual(result['status'], 'WRITE_COMPLETE_NOT_MERGED')
        writer.assert_called_once()
        self.assertEqual(self.files(), [])

    def test_02_owner_denial_no_retry(self):
        writer = mock.Mock(side_effect=Blocked('WRONG_AUTHENTICATED_ACTOR'))
        result = g.run_approved(None, approved(), 'draft', self.dir, writer=writer)
        writer.assert_called_once()
        self.assertEqual(result['failure_code'], 'WRONG_AUTHENTICATED_ACTOR')
        self.assertEqual(len(self.files()), 1)

    def test_03_changed_main_fail_draft(self):
        result = g.run_approved(None, approved(), 'draft', self.dir,
                      writer=mock.Mock(side_effect=Blocked('MAIN_CHANGED_OR_UNPROTECTED')))
        self.assertTrue(result['manual_reconciliation_required'])
        self.assertEqual(result['failure_code'], 'MAIN_CHANGED_OR_UNPROTECTED')

    def test_04_approval_absent_rejected(self):
        result = g.run_approved(None, approved(), 'draft', self.dir,
                      writer=mock.Mock(side_effect=Blocked('OWNER_APPROVAL_UNVERIFIED')))
        self.assertEqual(result['failure_code'], 'OWNER_APPROVAL_UNVERIFIED')

    def test_05_ruleset_rejected(self):
        result = g.run_approved(None, approved(), 'draft', self.dir,
                      writer=mock.Mock(side_effect=Blocked('RULESET_INACTIVE_OR_BYPASS')))
        self.assertEqual(result['failure_code'], 'RULESET_INACTIVE_OR_BYPASS')

    def test_06_head_rejected(self):
        result = g.run_approved(None, approved(), 'draft', self.dir,
                      writer=mock.Mock(side_effect=Blocked('BRANCH_HEAD_CHANGED')))
        self.assertEqual(result['failure_code'], 'BRANCH_HEAD_CHANGED')

    def test_07_candidate_sha_rejected(self):
        result = g.run_approved(None, approved(), 'draft', self.dir,
                      writer=mock.Mock(side_effect=Blocked('CANDIDATE_DIGEST_MISMATCH')))
        self.assertEqual(result['failure_code'], 'CANDIDATE_DIGEST_MISMATCH')

    def test_08_no_candidate_leak_in_draft(self):
        result = g.run_approved(None, approved(), 'secret_token_12345', self.dir,
                      writer=mock.Mock(side_effect=Exception('secret_token_12345')))
        text = self.files()[0].read_text()
        self.assertNotIn('secret_token_12345', text)
        self.assertEqual(result['failure_code'], 'UNKNOWN_FAILURE_RECONCILIATION_REQUIRED')

    def test_09_missing_local_dir_blocks_before_writer(self):
        w=mock.Mock()
        with self.assertRaises(Blocked):
            g.run_approved(None, approved(), 'x', self.dir/'absent', writer=w)
        w.assert_not_called()

    def test_10_no_overwrite_local_draft(self):
        record = {'schema': 1, 'source': 'failure'}
        with mock.patch.object(g.dt, 'datetime', wraps=g.dt.datetime) as fake:
            fake.now.return_value = g.dt.datetime.now(g.dt.timezone.utc)
            first=g._save_private(self.dir, record)
            with self.assertRaises(FileExistsError):
                g._save_private(self.dir, record)
        self.assertTrue(first.exists())

    def test_11_draft_private_permissions(self):
        g.run_approved(None, approved(), 'x', self.dir,
                      writer=mock.Mock(side_effect=Blocked('OWNER_APPROVAL_UNVERIFIED')))
        self.assertEqual(self.files()[0].stat().st_mode & 0o777, 0o600)

    def test_12_new_failure_draft_without_ledger_mutation(self):
        old=ledger()
        snapshot=json.dumps(old,sort_keys=True)
        result=g.propose_failure(old,failure(),self.dir)
        self.assertEqual(result['classification'], 'NEW_FAILURE_PROPOSED_NOT_COMMITTED')
        self.assertEqual(json.dumps(old,sort_keys=True),snapshot)
        self.assertEqual(len(self.files()),1)
        self.assertFalse(json.loads(self.files()[0].read_text())['authoritative_ledger_update'])

    def test_13_recurring_cause_flagged(self):
        old=ledger()
        record=failure('approval_provenance','other_failure')
        result=g.propose_failure(old,record,self.dir)
        self.assertEqual(result['classification'], 'RECURRING_CAUSE_REVIEW_LEARNING_MECHANISM')
        item=json.loads(self.files()[0].read_text())
        self.assertEqual(item['existing_failure_id'],'approval_provenance')
        self.assertEqual(len(old['failures']),4)

    def test_14_missing_cause_key_fails_closed(self):
        item=failure()
        del item['cause_key']
        with self.assertRaises(Blocked):
            g.propose_failure(ledger(),item,self.dir)
        self.assertEqual(self.files(),[])

    def test_15_missing_evidence_fails_closed(self):
        item=failure()
        item['evidence']=[]
        with self.assertRaises(Blocked):
            g.propose_failure(ledger(),item,self.dir)
        self.assertEqual(self.files(),[])

    def test_16_unverified_result_never_published(self):
        result=g.propose_failure(ledger(),failure(),self.dir)
        self.assertFalse(result['github_ledger_write_performed'])
        payload=json.loads(Path(result['draft_path']).read_text())
        self.assertFalse(payload['verified_root_cause'])

    def test_17_unknown_return_must_not_claim_success(self):
        r = g.run_approved(None, approved(), 'x', self.dir,
                  writer=mock.Mock(return_value={'status':'WRITE_COMPLETE_NOT_MERGED','commit_sha':'notsha'}))
        self.assertEqual(r['status'], 'BLOCKED_LOCAL_DRAFT_CREATED')
        self.assertEqual(r['failure_code'], 'UNKNOWN_WRITE_RESULT_RECONCILIATION_REQUIRED')
        self.assertEqual(len(self.files()), 1)

    def test_18_cli_apply_invalid_args_fail_closed(self):
        self.assertEqual(g.main(['--mode','apply','--draft-dir',str(self.dir)]),2)

    def test_19_cli_postcheck_only_local(self):
        led=self.dir/'ledger.json';fail=self.dir/'failure.json'
        led.write_text(json.dumps(ledger()))
        fail.write_text(json.dumps(failure()))
        rc=g.main(['--mode','postcheck','--draft-dir',str(self.dir),
                   '--ledger',str(led),'--failure',str(fail)])
        self.assertEqual(rc,0)
        self.assertEqual(len(self.files()),1)

    def test_20_no_auto_write_on_import(self):
        self.assertFalse(hasattr(g,'AUTO_GITHUB_WRITE'))


if __name__=='__main__':
    unittest.main()
