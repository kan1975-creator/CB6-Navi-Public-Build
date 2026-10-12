#!/usr/bin/env python3
"""Stage-1 only: twelve independent synthetic AC/DT pairs, never production evidence."""
import copy
import importlib.util
import pathlib
import unittest

P = pathlib.Path(__file__).resolve().parents[1] / "gates" / "verify_user_approval_before_fix.py"
spec = importlib.util.spec_from_file_location("approval_v", P)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
REPO = "kan1975-creator/CB6-Navi-Public-Build"
PLAN = {"proposed_change_id": "change-A", "basis_head": "a"*40,
        "planned_paths": ["v2/gates/a"], "forbidden_scope": ["v2/app"],
        "affected_domains": ["governance"]}
DIGEST = v.plan_digest(PLAN)
TRUST = {"plan": PLAN, "plan_sha256": DIGEST, "plan_commit_sha": "b"*40,
         "basis_head": "a"*40, "comment_id": 42, "repository": REPO,
         "issue_number": 5, "implementation_event_at": "2026-10-08T09:01:00Z",
         "implementation_event_verified": True, "plan_anchor_verified": True,
         "plan_path": "approval-plan.json"}
COMMENT = {"id": 42, "user": {"id": 313684924},
           "issue_url": "https://api.github.com/repos/" + REPO + "/issues/5",
           "created_at": "2026-10-08T09:00:00Z",
           "updated_at": "2026-10-08T09:00:00Z",
           "body": "CB6-APPROVE change-A " + DIGEST + " " + "b"*40}
DATA = {"proposed_change_id": "change-A", "basis_head": "a"*40,
        "approval": {"approval_id": "A-1", "approved_at": "2026-10-08T09:00:00Z",
                     "proposed_change_id": "change-A", "approved_change_summary": "exact change A",
                     "github_reference": "issue-comment:42"}}

def fixture():
    return copy.deepcopy((DATA, COMMENT, TRUST))

class TestApproval(unittest.TestCase):
    def assert_pair(self, mutate, expected):
        d, c, t = fixture()
        self.assertEqual(v.check(d, c, t), [], "AC normal fixture failed")
        mutate(d, c, t)
        errors = v.check(d, c, t)
        self.assertTrue(any(expected in e for e in errors), errors)

    def test_ac01_dt01_user(self):
        self.assert_pair(lambda d,c,t: c["user"].update(id=1), "GitHub user mismatch")

    def test_ac02_dt02_change_binding(self):
        self.assert_pair(lambda d,c,t: d.update(proposed_change_id="change-B"), "approval binding mismatch")

    def test_ac03_dt03_digest(self):
        self.assert_pair(lambda d,c,t: t.update(plan_sha256="0"*64), "plan hash mismatch")

    def test_ac04_dt04_basis_head(self):
        self.assert_pair(lambda d,c,t: t.update(basis_head="c"*40), "basis HEAD mismatch")

    def test_ac05_dt05_plan_content(self):
        self.assert_pair(lambda d,c,t: t["plan"]["planned_paths"].append("unexpected"), "plan hash mismatch")

    def test_ac06_dt06_posthoc(self):
        self.assert_pair(lambda d,c,t: t.update(implementation_event_at="2026-10-08T08:59:00Z"), "approval is not pre-implementation")

    def test_ac07_dt07_forged_timestamp(self):
        self.assert_pair(lambda d,c,t: d["approval"].update(approved_at="2026-10-08T08:59:00Z"), "approval timestamp mismatch")

    def test_ac08_dt08_edited(self):
        self.assert_pair(lambda d,c,t: c.update(updated_at="2026-10-08T09:02:00Z"), "edited comment")

    def test_ac09_dt09_wrong_issue(self):
        self.assert_pair(lambda d,c,t: c.update(issue_url="https://api.github.com/repos/" + REPO + "/issues/6"), "issue ownership mismatch")

    def test_ac10_dt10_api_failure(self):
        d,c,t = fixture()
        t.update(repository=REPO, plan_path="approval-plan.json")
        def valid_transport(repo, endpoint, token):
            import base64, json
            if endpoint.startswith("/issues/comments/"):
                return c
            if endpoint.startswith("/contents/"):
                return {"type":"file", "encoding":"base64",
                        "content":base64.b64encode(json.dumps(PLAN).encode()).decode()}
            return {"sha":"b"*40,"commit":{"committer":{"date":"2026-10-08T08:00:00Z"}}}
        self.assertEqual(v._verify_with_transport(d,t,"test",valid_transport),[])
        def broken(*args):
            raise OSError("simulated API outage")
        self.assertTrue(any("retrieval failed" in e for e in v._verify_with_transport(d,t,"test",broken)))

    def test_ac11_dt11_reference(self):
        self.assert_pair(lambda d,c,t: d["approval"].pop("github_reference"), "missing github approval reference")

    def test_ac12_dt12_legacy(self):
        d,c,t = fixture()
        legacy = {"proposed_change_id":"change-A",
                  "implementation_started_at":"2026-10-08T09:01:00Z",
                  "approval":{"approval_id":"A-1","approved_at":"2026-10-08T09:00:00Z",
                              "proposed_change_id":"change-A",
                              "approved_change_summary":"exact change A",
                              "github_reference":"commit-message: Approval-Ref=A-1"}}
        self.assertEqual(v.verify_legacy_structure(legacy),["legacy evidence is not authenticated approval"])
        self.assertTrue(v.check(legacy))
        legacy["approval"]["proposed_change_id"] = "change-B"
        self.assertIn("approval binding mismatch",v.verify_legacy_structure(legacy))

    def test_missing_comment_and_trust_provenance(self):
        d,c,t = fixture()
        self.assertTrue(v.check(d,{},t))
        t["plan_anchor_verified"] = False
        self.assertIn("plan anchor not independently verified",v.check(d,c,t))
        self.assertEqual(v.main(["verifier"]),1)

    def test_plan_commit_time_and_mock_production_separation(self):
        d,c,t = fixture()
        def invalid_commit(repo,endpoint,token):
            if endpoint.startswith("/issues/comments/"): return c
            if endpoint.startswith("/contents/"): return {"type":"file","encoding":"base64","content":"e30="}
            return {"sha":"b"*40,"commit":{"committer":{"date":"2026-10-08T09:05:00Z"}}}
        self.assertTrue(v._verify_with_transport(d,t,"test",invalid_commit))
        import inspect
        self.assertNotIn("fetch",inspect.signature(v.verify_live).parameters)


    def test_at01_base64_github_folding_and_invalid(self):
        import base64, json
        d,c,t = fixture()
        encoded = base64.b64encode(json.dumps(PLAN).encode()).decode()
        def run(blob):
            def fetch(repo,endpoint,token):
                if endpoint.startswith("/issues/comments/"): return c
                if endpoint.startswith("/contents/"): return {"type":"file","encoding":"base64","content":blob}
                return {"sha":"b"*40,"commit":{"committer":{"date":"2026-10-08T08:00:00Z"}}}
            return v._verify_with_transport(d,t,"test",fetch)
        self.assertEqual(run(encoded), [])
        folded = "\r\n".join(encoded[i:i+40] for i in range(0,len(encoded),40))
        self.assertEqual(run(folded), [])
        for broken in (encoded[:8]+"!"+encoded[8:], encoded[:-1], base64.b64encode(b"not-json").decode()):
            self.assertTrue(run(broken), "invalid plan content accepted")

    def test_at02_http_status_fail_closed(self):
        import urllib.error
        d,c,t = fixture()
        for status in (401,403,404,429,500,503):
            with self.subTest(status=status):
                def fetch(repo,endpoint,token):
                    raise urllib.error.HTTPError("https://api.github.com",status,"simulated",{},None)
                errors=v._verify_with_transport(d,t,"test",fetch)
                self.assertTrue(any("retrieval failed" in e for e in errors),errors)

    def test_at03_deleted_comment_and_wrong_binding(self):
        import urllib.error
        d,c,t = fixture()
        def deleted(repo,endpoint,token):
            raise urllib.error.HTTPError("https://api.github.com",404,"not found",{},None)
        self.assertTrue(v._verify_with_transport(d,t,"test",deleted))
        c["issue_url"]="https://api.github.com/repos/"+REPO+"/issues/6"
        self.assertIn("issue ownership mismatch",v.check(d,c,t))
        c["issue_url"]=COMMENT["issue_url"]
        c["id"]=43
        self.assertIn("comment ID mismatch",v.check(d,c,t))

    def test_at04_legacy_structure_never_authenticated(self):
        d,c,t=fixture()
        legacy={"proposed_change_id":"change-A","implementation_started_at":"2026-10-08T09:01:00Z",
                "approval":{"approval_id":"A-1","approved_at":"2026-10-08T09:00:00Z",
                            "proposed_change_id":"change-A","approved_change_summary":"exact",
                            "github_reference":"commit-message: Approval-Ref=A-1"}}
        self.assertEqual(v.verify_legacy_structure(legacy),["legacy evidence is not authenticated approval"])
        self.assertTrue(v.check(legacy))
        legacy["approval"]["approved_at"]="2026-10-08T09:02:00Z"
        self.assertIn("approval is not pre-implementation",v.verify_legacy_structure(legacy))

    def test_at05_candidate_active_boundary(self):
        self.assertEqual(v.CONTRACT["status"],"CANDIDATE")
        self.assertEqual(v.CONTRACT["stage1"]["overall_status"],"ENFORCEMENT_UNVERIFIED")
        self.assertIn("remains ACTIVE",v.CONTRACT["stage1"]["active_rule_boundary"])
        self.assertEqual(v.CONTRACT["stage1"]["ac_count"],12)
        self.assertEqual(v.CONTRACT["stage1"]["dt_count"],12)


class TestStage2ProductionFailClosed(unittest.TestCase):
    """These are local counterfactual tests, NOT authenticated GitHub evidence."""

    def setUp(self):
        self.d, self.c, self.t = fixture()
        self.t.update(pr_number=5, pr_head_sha="c"*40, pr_base_sha="a"*40,
                      pr_base_ref="cb6-v2-clean")
        self.changed=[{"filename": "v2/gates/a", "status": "modified"}]
        self.state={"number":5, "state":"open", "changed_files":len(self.changed),
                    "head":{"sha":"c"*40},
                    "base":{"sha":"a"*40,"ref":"cb6-v2-clean",
                            "repo":{"full_name":REPO}}}
        self.calls=0

    def api(self, repo, endpoint, token):
        if repo != REPO: raise OSError("wrong repository")
        self.calls+=1
        if "/files?" in endpoint: return copy.deepcopy(self.changed)
        if endpoint=="/pulls/5": return copy.deepcopy(self.state)
        raise OSError("unexpected read endpoint")

    def verify_diff(self):
        return v.verify_pr_diff_with_transport(self.d,self.t,"synthetic",self.api)

    def assert_block(self, errors):
        self.assertTrue(errors, 'unexpected scope acceptance')
        self.assertIn('PR diff evidence rejected:',errors[0])

    def test_e3_synthetic_positive_scope_does_not_authorize_production(self):
        self.assertEqual(self.verify_diff(),[])
        self.assertEqual(self.calls,3)
        self.assertIn('PROVENANCE_BLOCKED',v.verify_live(self.d,self.t,'synthetic')[0])

    def test_e3_self_reported_trust_flags_always_production_block(self):
        for mode in ('none','both_true','fake_extra_anchor','fake_start_run'):
            with self.subTest(mode=mode):
                t=copy.deepcopy(self.t)
                t.update(trust_anchor_provisioned_externally=True,
                         plan_anchor_verified=True,implementation_event_verified=True,
                         implementation_run_id=37442886846,
                         protected_ref='refs/heads/cb6-v2-clean')
                self.assertIn('PROVENANCE_BLOCKED',v.verify_live(self.d,t,'fake-gh-token')[0])

    def test_e3_bad_base_head(self):
        self.state['base']['sha']='d'*40
        self.assert_block(self.verify_diff())

    def test_e3_bad_pr_head(self):
        self.state['head']['sha']='d'*40
        self.assert_block(self.verify_diff())

    def test_e3_head_moved_between_reads(self):
        def moving(repo,endpoint,token):
            result=self.api(repo,endpoint,token)
            if endpoint=='/pulls/5' and self.calls >= 3:
                result['head']['sha']='f'*40
            return result
        self.assert_block(v.verify_pr_diff_with_transport(self.d,self.t,'fake',moving))

    def test_ir_rename_from_forbidden_into_approved_path_rejects(self):
        self.changed=[{"filename":"v2/gates/a", "status":"renamed",
                       "previous_filename":"v2/app"}]
        self.assert_block(self.verify_diff())

    def test_ir_rename_from_unplanned_path_rejects(self):
        self.changed=[{"filename":"v2/gates/a", "status":"renamed",
                       "previous_filename":"v2/other/a"}]
        self.assert_block(self.verify_diff())

    def test_ir_rename_requires_explicitly_planned_both_endpoints(self):
        self.changed=[{"filename":"v2/gates/a", "status":"renamed",
                       "previous_filename":"v2/gates/original"}]
        self.t['plan']['planned_paths']=['v2/gates/a','v2/gates/original']
        self.assertEqual(self.verify_diff(), [])  # Synthetic scope only, no approval.
        self.assertIn('PROVENANCE_BLOCKED', v.verify_live(self.d,self.t,'fake')[0])

    def test_ir_rename_with_missing_or_unsafe_source_rejects(self):
        for previous in (None, '', '../secret', '/secret', 'v2//app', 'v2/./app'):
            with self.subTest(previous=previous):
                self.changed=[{"filename":"v2/gates/a", "status":"renamed"}]
                if previous is not None:
                    self.changed[0]['previous_filename']=previous
                self.assert_block(self.verify_diff())

    def test_ir_rename_source_on_nonrenamed_entry_rejects(self):
        self.changed=[{"filename":"v2/gates/a", "status":"modified",
                       "previous_filename":"v2/app"}]
        self.assert_block(self.verify_diff())

    def test_ir_same_base_sha_different_base_ref_rejects(self):
        self.state['base']['ref']='main'  # base SHA is unchanged.
        self.assert_block(self.verify_diff())

    def test_ir_base_ref_drift_between_api_reads_rejects(self):
        def drift(repo, endpoint, token):
            result=self.api(repo,endpoint,token)
            if endpoint=='/pulls/5' and self.calls >= 3:
                result['base']['ref']='main'
            return result
        self.assert_block(v.verify_pr_diff_with_transport(self.d,self.t,'fake',drift))

    def test_e3_unauthorized_extra_path(self):
        self.changed.append({'filename': 'app/src/main/java/injected.java', 'status':'modified'})
        self.state['changed_files']=2
        self.assert_block(self.verify_diff())

    def test_e3_forbidden_scope_even_if_in_plan(self):
        self.changed=[{'filename':'v2/app', 'status':'modified'}]
        self.state['changed_files']=1
        self.t['plan']['planned_paths']=['v2/app']
        self.assert_block(self.verify_diff())

    def test_e3_partial_file_page(self):
        self.state['changed_files']=2
        self.assert_block(self.verify_diff())

    def test_ir2_missing_null_and_unknown_status_reject(self):
        for status in ("missing", None, "copied", "changed", "", 0, True):
            with self.subTest(status=status):
                item = {"filename":"v2/gates/a"}
                if status != "missing":
                    item["status"] = status
                self.changed = [item]
                self.assert_block(self.verify_diff())

    def test_ir2_explicit_supported_statuses_are_not_regressed(self):
        for status in ("added", "modified", "removed"):
            with self.subTest(status=status):
                self.changed = [{"filename":"v2/gates/a", "status":status}]
                self.assertEqual(self.verify_diff(), [])
                self.assertIn("PROVENANCE_BLOCKED", v.verify_live(self.d,self.t,"fake")[0])

    def test_ir2_forbidden_descendant_even_when_planned_rejects(self):
        for forbidden, path in (("v2/app", "v2/app/private.py"),
                                ("v2/app/", "v2/app/private.py"),
                                ("v2/app", "v2/app/deep/private.py"),
                                ("v2/app", "v2/app")):
            with self.subTest(forbidden=forbidden, path=path):
                self.t['plan']['forbidden_scope'] = [forbidden]
                self.t['plan']['planned_paths'] = [path]
                self.changed = [{"filename":path, "status":"modified"}]
                self.assert_block(self.verify_diff())

    def test_ir2_rename_from_forbidden_descendant_rejects(self):
        self.changed = [{"filename":"v2/gates/a", "status":"renamed",
                         "previous_filename":"v2/app/private.py"}]
        self.t['plan']['planned_paths'] = ["v2/app/private.py", "v2/gates/a"]
        self.assert_block(self.verify_diff())

    def test_ir2_forbidden_sibling_prefix_is_not_overblocked(self):
        self.changed = [{"filename":"v2/app2/private.py", "status":"modified"}]
        self.t['plan']['planned_paths'] = ["v2/app2/private.py"]
        self.assertEqual(self.verify_diff(), [])  # synthetic helper, not production
        self.assertIn("PROVENANCE_BLOCKED", v.verify_live(self.d,self.t,"fake")[0])

    def test_ir2_trusted_flags_still_cannot_unblock_production(self):
        t = copy.deepcopy(self.t)
        t.update(trust_anchor_provisioned_externally=True,
                 implementation_event_verified=True, plan_anchor_verified=True)
        self.assertIn("PROVENANCE_BLOCKED", v.verify_live(self.d,t,"fake")[0])

    def test_e3_wrong_repository(self):
        self.state['base']['repo']['full_name']='outsider/fork'
        self.assert_block(self.verify_diff())

    def test_e3_duplicate_diff_filename(self):
        self.changed.append({'filename':'v2/gates/a','status':'modified'})
        self.state['changed_files']=2
        self.assert_block(self.verify_diff())

    def test_e3_base_plan_mismatch(self):
        self.t['plan']['basis_head']='d'*40
        self.assert_block(self.verify_diff())

    def test_e3_unsafe_path(self):
        self.changed=[{'filename':'../escape','status':'modified'}]
        self.assert_block(self.verify_diff())

    def test_e3_api_failure_denies(self):
        for code in (401,403,404,429,500,503):
            with self.subTest(code=code):
                import urllib.error
                def outage(repo,endpoint,token):
                    raise urllib.error.HTTPError('https://api.github.com',code,'blocked',{},None)
                self.assert_block(v.verify_pr_diff_with_transport(self.d,self.t,'fake',outage))

    def test_e3_malformed_pr_count_rejects(self):
        for val in (True,0,301,'2',None):
            with self.subTest(value=val):
                self.state['changed_files']=val
                self.assert_block(self.verify_diff())

    def test_e3_candidate_workflow_is_nonprivileged_and_nonbypass(self):
        wf=v.ROOT/'.github/workflows/cb6_approval_enforcement.yml'
        self.assertTrue(wf.is_file())
        text=wf.read_text()
        self.assertIn('pull_request_target:',text)
        self.assertIn('ref: ${{ github.event.pull_request.base.sha }}',text)
        self.assertIn('persist-credentials: false',text)
        self.assertIn('python3 -B v2/gates/verify_user_approval_before_fix.py',text)
        self.assertNotIn('continue-on-error: true',text)
        self.assertNotIn('github.event.pull_request.head.sha',text)
        self.assertNotIn('pull-requests: write',text)
        self.assertNotIn('contents: write',text)
        self.assertNotIn('secrets:',text)
        self.assertIn('production_enforcement',v.CONTRACT['stage2_fail_closed_candidate'])
        self.assertEqual(v.CONTRACT['stage2_fail_closed_candidate']['production_enforcement'],
                         'BLOCKED_UNTIL_INDEPENDENT_PROTECTED_TRUST_ANCHOR')

    def test_e3_destructive_workflow_head_checkout_mutation(self):
        wf=(v.ROOT/'.github/workflows/cb6_approval_enforcement.yml').read_text()
        tampered=wf.replace('ref: ${{ github.event.pull_request.base.sha }}',
                            'ref: ${{ github.event.pull_request.head.sha }}')
        def no_head_checkout(value):
            return ('ref: ${{ github.event.pull_request.base.sha }}' in value and
                    'ref: ${{ github.event.pull_request.head.sha }}' not in value)
        self.assertTrue(no_head_checkout(wf))
        self.assertFalse(no_head_checkout(tampered))

    def test_e3_destructive_workflow_continue_on_error_mutation(self):
        wf=(v.ROOT/'.github/workflows/cb6_approval_enforcement.yml').read_text()
        tampered=wf.replace('run: python3 -B v2/gates/verify_user_approval_before_fix.py',
                            'continue-on-error: true\n        run: python3 -B v2/gates/verify_user_approval_before_fix.py')
        def deny_continuing(value):
            return 'continue-on-error: true' not in value
        self.assertTrue(deny_continuing(wf))
        self.assertFalse(deny_continuing(tampered))

    def test_e3_production_entrypoint_unconditional_block_does_not_invoke_mock(self):
        from unittest.mock import patch
        with patch.object(v,'github_get',side_effect=AssertionError('unexpected mock transport')):
            self.assertIn('PROVENANCE_BLOCKED',v.verify_live(self.d,self.t,'fake')[0])

    def test_e3_production_cli_with_self_asserted_flags_must_fail(self):
        import tempfile,json,os
        from unittest.mock import patch
        # Temporary runtime fixtures are outside the tracked four source paths.
        with tempfile.TemporaryDirectory(prefix='cb6_e3_runtime_') as td:
            d=pathlib.Path(td)/'evidence.json'; t=pathlib.Path(td)/'trusted.json'
            d.write_text(json.dumps(self.d))
            forged=copy.deepcopy(self.t)
            forged.update(trust_anchor_provisioned_externally=True,
                          implementation_event_verified=True,plan_anchor_verified=True)
            t.write_text(json.dumps(forged))
            with patch.dict(os.environ, {'GITHUB_TOKEN':'fake-token'}):
                with patch.object(v, 'github_get', side_effect=AssertionError('must not call fake network')):
                    self.assertEqual(v.main(['verify',str(d),str(t)]),1)


class TestProtectedLiveHandoffCandidate(unittest.TestCase):
    """ONLY the new read-only bridge; synthetic responses never authorize PASS."""

    def setUp(self):
        import base64
        self.d, self.comment, self.trusted = fixture()
        self.trusted.update(pr_number=5, pr_head_sha="c"*40,
                            pr_base_sha="a"*40, pr_base_ref="cb6-v2-clean")
        self.trusted["plan"]["basis_head"] = "a"*40
        self.trusted["plan_sha256"] = v.plan_digest(self.trusted["plan"])
        self.comment["body"] = ("CB6-APPROVE change-A " +
                                self.trusted["plan_sha256"] + " " + "b"*40)
        self.changed = [{"filename":"v2/gates/a","status":"modified"}]
        self.pr = {"number":5, "state":"open", "changed_files":1,
                   "head":{"sha":"c"*40},
                   "base":{"sha":"a"*40,"ref":"cb6-v2-clean",
                           "repo":{"full_name":REPO}}}
        self.plan_blob = base64.b64encode(
            __import__('json').dumps(self.trusted['plan']).encode()).decode()
        self.end_comment = copy.deepcopy(self.comment)
        self.requests = []

    def api(self, repo, endpoint, token):
        self.assertEqual(repo, REPO)
        self.assertEqual(token, 'fake')
        self.requests.append(endpoint)
        if endpoint == '/issues/comments/42':
            if self.requests.count(endpoint) > 1:
                return copy.deepcopy(self.end_comment)
            return copy.deepcopy(self.comment)
        if endpoint == '/contents/approval-plan.json?ref=' + 'b'*40:
            return {'encoding':'base64','type':'file','content':self.plan_blob}
        if endpoint == '/commits/' + 'b'*40:
            return {'sha':'b'*40, 'commit':{'committer':{'date':'2026-10-08T08:59:00Z'}}}
        if endpoint == '/pulls/5': return copy.deepcopy(self.pr)
        if endpoint == '/pulls/5/files?per_page=100&page=1':
            return copy.deepcopy(self.changed)
        raise OSError('unexpected read endpoint')

    def inspect(self, trusted=None, api=None):
        return v.inspect_live_provenance_candidate(
            self.d, self.trusted if trusted is None else trusted,
            'fake', self.api if api is None else api)

    def test_connected_reads_still_cannot_grant_production_pass(self):
        claimed=copy.deepcopy(self.trusted)
        claimed.update(trust_anchor_provisioned_externally=True,
                       implementation_event_verified=True,
                       plan_anchor_verified=True,revoked=False,
                       issuer_status='success')
        result=self.inspect(trusted=claimed)
        self.assertEqual(len(result),1)
        self.assertIn('PROVENANCE_BLOCKED',result[0])
        self.assertEqual(self.requests.count('/issues/comments/42'),2)
        self.assertEqual(self.requests.count('/pulls/5'),2)
        # Actual production entrypoint must remain an unconditional blocker.
        self.assertIn('PROVENANCE_BLOCKED',v.verify_live(self.d,claimed,'fake')[0])

    def test_approval_modified_during_scope_review_rejects(self):
        self.end_comment['updated_at']='2026-10-08T09:05:00Z'
        result=self.inspect()
        self.assertIn('edited comment',str(result))
        self.assertIn('PROVENANCE_BLOCKED',str(result))

    def test_live_plan_scope_mismatch_rejects_before_api(self):
        forged=copy.deepcopy(self.trusted)
        forged['plan']['planned_paths']=['v2/forged.py']
        result=self.inspect(trusted=forged)
        self.assertIn('scope plan hash mismatch',str(result))
        self.assertFalse(self.requests)

    def test_changed_pr_head_rejects_and_stays_blocked(self):
        self.pr['head']['sha']='d'*40
        result=self.inspect()
        self.assertIn('PR HEAD mismatch',str(result))
        self.assertIn('PROVENANCE_BLOCKED',str(result))

    def test_comment_deleted_or_api_failure_stays_blocked(self):
        import urllib.error
        def deleted(repo, endpoint, token):
            if endpoint == '/issues/comments/42':
                raise urllib.error.HTTPError('https://api.github.com',404,'missing',{},None)
            return self.api(repo,endpoint,token)
        result=self.inspect(api=deleted)
        self.assertIn('PROVENANCE_BLOCKED',str(result))
        self.assertIn('404',str(result))

    def test_missing_protected_input_and_self_asserted_revocation(self):
        forged=copy.deepcopy(self.trusted)
        forged.update(revoked=False,plan_anchor_verified=True,
                      implementation_event_verified=True)
        forged['repository']='outsider/fork'
        self.assertIn('PROVENANCE_BLOCKED',str(self.inspect(trusted=forged)))
        self.assertFalse(self.requests)
        self.assertIn('PROVENANCE_BLOCKED',str(self.inspect()))



class TestNewC05C07Bridge(unittest.TestCase):
    """ONLY new C-05/C-07 connector behavior, not the previous passing suite."""
    def test_authenticated_blocking_check_still_blocks_production(self):
        d = {"repository": REPO, "pr_head_sha": "a"*40,
             "proposed_change_id": "change-A", "plan_sha256": "c"*64}
        def api(repo, endpoint, token):
            self.assertEqual(endpoint, "/commits/" + "a"*40 + "/check-runs?per_page=100")
            return {"total_count": 1, "check_runs": [{
                "name":"CB6 Approval Enforcement", "head_sha":"a"*40,
                "external_id":"CB6-BLOCKED:change-A:"+"c"*64+":"+"a"*40,
                "app":{"id":123}, "status":"completed", "conclusion":"failure"}]}
        self.assertIn("PROVENANCE_BLOCKED", v.observe_independent_check_candidate(
            d, "token", api, 123)[0])

    def test_forged_and_stale_check_rejected(self):
        d = {"repository": REPO, "pr_head_sha": "a"*40,
             "proposed_change_id": "change-A", "plan_sha256": "c"*64}
        for forged in (
            {"name":"CB6 Approval Enforcement", "head_sha":"b"*40,
             "external_id":"CB6-BLOCKED:change-A:"+"c"*64+":"+"a"*40,
             "app":{"id":123}, "status":"completed", "conclusion":"failure"},
            {"name":"CB6 Approval Enforcement", "head_sha":"a"*40,
                "external_id":"CB6-BLOCKED:change-A:"+"c"*64+":"+"a"*40,
             "app":{"id":999}, "status":"completed", "conclusion":"failure"},
            {"name":"CB6 Approval Enforcement", "head_sha":"a"*40,
             "external_id":"CB6-BLOCKED:change-A:"+"c"*64+":"+"a"*40,
             "app":{"id":123}, "status":"completed", "conclusion":"success"},
            {"name":"CB6 Approval Enforcement", "head_sha":"a"*40,
             "external_id":"CB6-BLOCKED:change-B:"+"c"*64+":"+"a"*40,
             "app":{"id":123}, "status":"completed", "conclusion":"failure"},
        ):
            with self.subTest(forged=forged):
                fetch=lambda repo, endpoint, token: {"total_count":1,"check_runs":[forged]}
                e=v.observe_independent_check_candidate(d,"token",fetch,123)
                self.assertIn("rejected",e[0]);self.assertIn("PROVENANCE_BLOCKED",e[-1])

    def test_incomplete_check_and_missing_anchor_rejected(self):
        d = {"repository": REPO, "pr_head_sha": "a"*40,
             "proposed_change_id": "change-A", "plan_sha256": "c"*64}
        for data in ({"total_count":101,"check_runs":[]},
                     {"total_count":2,"check_runs":[]},
                     {"total_count":0,"check_runs":[]}):
            errors=v.observe_independent_check_candidate(d,"token",lambda *args:data,123)
            self.assertIn("PROVENANCE_BLOCKED",errors[-1])
        self.assertIn("App ID unprovisioned",str(v.observe_independent_check_candidate(
            d,"token",lambda *args:None,None)))

    def test_sql_decision_ledger_is_candidate_and_immutable(self):
        import sqlite3
        schema=(P.parents[2]/"db"/"schema.sql").read_text()
        db=sqlite3.connect(":memory:")
        db.executescript(schema)
        row=("00000000-0000-4000-8000-000000000001","f"*64,101,1,"a"*40,"b"*40,
             "change-A","c"*64,"d"*40,"APPROVE",42,313684924,"2026-10-12T01:00:00Z")
        sql="""INSERT INTO issuer_decision_event_candidate
          (delivery_id,body_sha256,repository_id,pr_number,pr_head_sha,basis_head,
           change_id,plan_sha256,plan_commit_sha,decision,github_comment_id,
           github_actor_id,github_created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        db.execute(sql,row)
        with self.assertRaises(sqlite3.IntegrityError): db.execute(sql,row)
        with self.assertRaises(sqlite3.IntegrityError): db.execute(
            "UPDATE issuer_decision_event_candidate SET decision='REVOKE'")
        with self.assertRaises(sqlite3.IntegrityError): db.execute(
            "DELETE FROM issuer_decision_event_candidate")
        self.assertEqual(db.execute("SELECT gate_verdict FROM issuer_decision_event_candidate").fetchone(),
                         ("BLOCKED_UNVERIFIED",))
        for idx,val in ((11,1),(3,0),(7,"g"*64),(9,"GRANT")):
            bad=list(row);bad[0]="00000000-0000-4000-8000-000000000002";bad[1]="e"*64
            bad[10]=43;bad[idx]=val
            with self.subTest(idx=idx), self.assertRaises(sqlite3.IntegrityError):
                db.execute(sql,bad)
        db.close()


class TestNewFiveFileTimelineDelta(unittest.TestCase):
    """Only new 5-file candidate boundary, not earlier accepted AC/DT tests."""

    @staticmethod
    def identity():
        return {"repository_id": 101, "pr_number": 5, "change_id": "change-A",
                "plan_sha256": "c"*64, "plan_commit_sha": "d"*40,
                "head_sha": "a"*40, "basis_head": "b"*40}

    @classmethod
    def row(cls, timestamp, decision=None):
        d = cls.identity()
        d["pr_head_sha"] = d.pop("head_sha")
        d["github_created_at"] = timestamp
        if decision is not None:
            d["decision"] = decision
        return d

    def test_prestart_approval_still_blocks_without_independent_authority(self):
        approval = self.row("2026-10-12T10:00:00Z", "APPROVE")
        start = self.row("2026-10-12T10:01:00Z")
        result = v.inspect_captured_timeline_candidate(self.identity(), [start], [approval])
        self.assertEqual(len(result), 1)
        self.assertIn("PROVENANCE_BLOCKED", result[-1])

    def test_captured_revocation_blocks(self):
        approval = self.row("2026-10-12T10:00:00Z", "APPROVE")
        revoke = self.row("2026-10-12T10:03:00Z", "REVOKE")
        start = self.row("2026-10-12T10:01:00Z")
        result = v.inspect_captured_timeline_candidate(self.identity(), [start], [approval, revoke])
        self.assertIn("recorded revocation blocks approval", result)
        self.assertIn("PROVENANCE_BLOCKED", result[-1])

    def test_posthoc_approval_rejected(self):
        approval = self.row("2026-10-12T10:02:00Z", "APPROVE")
        start = self.row("2026-10-12T10:01:00Z")
        result = v.inspect_captured_timeline_candidate(self.identity(), [start], [approval])
        self.assertIn("approval not before captured start", result)

    def test_stale_head_and_crossplan_rows_rejected(self):
        approval = self.row("2026-10-12T10:00:00Z", "APPROVE")
        start = self.row("2026-10-12T10:01:00Z")
        approval["pr_head_sha"] = "b"*40
        self.assertIn("stale PR HEAD", str(v.inspect_captured_timeline_candidate(
            self.identity(), [start], [approval])))
        approval["pr_head_sha"] = "a"*40
        approval["plan_sha256"] = "e"*64
        self.assertIn("cross-plan", str(v.inspect_captured_timeline_candidate(
            self.identity(), [start], [approval])))
        approval["plan_sha256"] = "c"*64
        approval["basis_head"] = "f"*40
        self.assertIn("cross-plan", str(v.inspect_captured_timeline_candidate(
            self.identity(), [start], [approval])))

    def test_missing_start_and_approval_cannot_grant_pass(self):
        result = v.inspect_captured_timeline_candidate(self.identity(), [], [])
        self.assertIn("missing or ambiguous captured start", result)
        self.assertIn("missing or ambiguous captured approval", result)
        self.assertIn("PROVENANCE_BLOCKED", result[-1])

    @staticmethod
    def make_db():
        import sqlite3
        db = sqlite3.connect(":memory:")
        db.executescript((P.parents[2]/"db"/"schema.sql").read_text())
        return db

    @staticmethod
    def insert_decision(db, delivery, body, comment, timestamp, decision):
        return db.execute("""INSERT INTO issuer_decision_event_candidate
             (delivery_id, body_sha256, repository_id, pr_number, pr_head_sha,
              basis_head, change_id, plan_sha256, plan_commit_sha, decision,
              github_comment_id, github_actor_id, github_created_at)
             VALUES (?, ?, 101, 5, ?, ?, 'change-A', ?, ?, ?, ?, 313684924, ?)""",
            (delivery, body, "a"*40, "b"*40, "c"*64, "d"*40, decision, comment, timestamp))

    @staticmethod
    def insert_start(db, delivery, body, comment, timestamp):
        return db.execute("""INSERT INTO issuer_start_observation_candidate
             (delivery_id, body_sha256, repository_id, pr_number, pr_head_sha,
              basis_head, change_id, plan_sha256, plan_commit_sha,
              github_comment_id, github_actor_id, github_created_at)
             VALUES (?, ?, 101, 5, ?, ?, 'change-A', ?, ?, ?, 313684924, ?)""",
            (delivery, body, "a"*40, "b"*40, "c"*64, "d"*40, comment, timestamp))

    def test_sql_atomic_revocation_before_approval(self):
        import sqlite3
        db = self.make_db()
        self.insert_decision(db, "revoke-id", "f"*64, 40, "2026-10-12T10:03:00Z", "REVOKE")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "prior_revocation"):
            self.insert_decision(db, "approve-id", "e"*64, 41, "2026-10-12T10:00:00Z", "APPROVE")
        self.assertEqual(db.execute("SELECT count(*) FROM issuer_decision_event_candidate").fetchone()[0], 1)
        db.close()

    def test_sql_late_approval_rejected_start_first(self):
        import sqlite3
        db = self.make_db()
        self.insert_start(db, "start-id", "f"*64, 40, "2026-10-12T10:01:00Z")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "approval_not_before_captured_start"):
            self.insert_decision(db, "approve-id", "e"*64, 41, "2026-10-12T10:02:00Z", "APPROVE")
        db.close()

    def test_sql_late_approval_rejected_approval_first(self):
        import sqlite3
        db = self.make_db()
        self.insert_decision(db, "approve-id", "e"*64, 41, "2026-10-12T10:02:00Z", "APPROVE")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "observed_start_not_after_approval"):
            self.insert_start(db, "start-id", "f"*64, 40, "2026-10-12T10:01:00Z")
        db.close()

    def test_sql_start_is_immutable_and_non_authorizing(self):
        import sqlite3
        db = self.make_db()
        self.insert_start(db, "start-id", "f"*64, 40, "2026-10-12T10:01:00Z")
        self.assertEqual(db.execute("SELECT gate_verdict FROM issuer_start_observation_candidate").fetchone(),
                         ("BLOCKED_UNVERIFIED",))
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("DELETE FROM issuer_start_observation_candidate")
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("UPDATE issuer_start_observation_candidate SET github_created_at='2026-10-12T01:00:00Z'")
        db.close()

    def test_candidate_workflow_guarantees_failure(self):
        text = (P.parents[2]/".github"/"workflows"/"cb6_approval_enforcement.yml").read_text()
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("if: always()", text)
        self.assertIn("exit 1", text)
        self.assertNotIn("continue-on-error: true", text)


class TestNewBlockedCheckHandshakeOnly(unittest.TestCase):
    """NEW delta only: Check identity handshake is never a PASS source."""

    def setUp(self):
        self.d = {"repository": REPO, "pr_number": 5, "pr_head_sha": "a"*40,
                  "pr_base_sha": "b"*40, "pr_base_ref": "cb6-v2-clean",
                  "proposed_change_id": "change-A", "plan_sha256": "c"*64}
        self.check = {"name": "CB6 Approval Enforcement", "head_sha": "a"*40,
                      "external_id": "CB6-BLOCKED:change-A:" + "c"*64 + ":" + "a"*40,
                      "status": "completed", "conclusion": "failure", "app": {"id": 123}}
        self.pr = {"number": 5, "state": "open", "head": {"sha": "a"*40},
                   "base": {"sha": "b"*40, "ref": "cb6-v2-clean",
                            "repo": {"id": 101, "full_name": REPO}}}

    def api(self, repo, endpoint, token):
        self.assertEqual(repo, REPO)
        if endpoint == "/pulls/5":
            return copy.deepcopy(self.pr)
        if endpoint == "/commits/" + "a"*40 + "/check-runs?per_page=100":
            return {"total_count": 1, "check_runs": [copy.deepcopy(self.check)]}
        raise AssertionError("unexpected endpoint " + endpoint)

    def test_new_blocking_handshake_is_not_authorization(self):
        result = v.inspect_live_blocked_issuer_candidate(self.d, "token", self.api, 123, 101)
        self.assertEqual(len(result), 1)
        self.assertIn("PROVENANCE_BLOCKED", result[0])

    def test_new_stale_and_cross_plan_check_rejected(self):
        for field, value in (("head_sha", "f"*40),
                             ("external_id", "CB6-BLOCKED:other:" + "c"*64 + ":" + "a"*40),
                             ("conclusion", "success"),
                             ("app", {"id": 999})):
            with self.subTest(field=field):
                old = self.check[field]; self.check[field] = value
                result = v.inspect_live_blocked_issuer_candidate(self.d, "token", self.api, 123, 101)
                self.assertIn("rejected", result[0])
                self.assertIn("PROVENANCE_BLOCKED", result[-1])
                self.check[field] = old

    def test_new_stale_live_pr_and_missing_app_id_rejected(self):
        for field, value in (("sha", "f"*40), ("sha", "a"*40)):
            self.pr["head"][field] = value
            result = v.inspect_live_blocked_issuer_candidate(self.d, "token", self.api, 123, 101)
            self.assertIn("PROVENANCE_BLOCKED", result[-1])
            if value != "a"*40:
                self.assertIn("rejected", result[0])
        self.assertIn("not independently configured", str(
            v.inspect_live_blocked_issuer_candidate(self.d, "token", self.api, None, 101)))
        self.assertIn("repository ID not independently configured", str(
            v.inspect_live_blocked_issuer_candidate(self.d, "token", self.api, 123, None)))

    def test_new_changed_live_pr_between_reads_rejected(self):
        count = 0
        def swap(repo, endpoint, token):
            nonlocal count
            if endpoint == "/pulls/5":
                count += 1
                p = copy.deepcopy(self.pr)
                if count == 2: p["head"]["sha"] = "e"*40
                return p
            return self.api(repo,endpoint,token)
        result = v.inspect_live_blocked_issuer_candidate(self.d,"token",swap,123,101)
        self.assertIn("rejected", result[0])
        self.assertIn("PROVENANCE_BLOCKED", result[-1])

if __name__ == "__main__":
    unittest.main()
