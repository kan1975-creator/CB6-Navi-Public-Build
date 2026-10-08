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

if __name__ == "__main__":
    unittest.main()
