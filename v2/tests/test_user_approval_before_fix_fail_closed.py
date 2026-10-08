#!/usr/bin/env python3
"""AC-01..12 and DT-01..12: stage-1 verifier-only tests."""
import copy
import importlib.util
import pathlib
import unittest

P = pathlib.Path(__file__).resolve().parents[1] / "gates" / "verify_user_approval_before_fix.py"
spec = importlib.util.spec_from_file_location("approval_v", P)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

PLAN = {"proposed_change_id":"change-A","basis_head":"a"*40,
        "planned_paths":["v2/gates/a"],"forbidden_scope":["v2/app"],
        "affected_domains":["governance"]}
DIGEST = v.plan_digest(PLAN)
TRUST = {"plan":PLAN,"plan_sha256":DIGEST,"plan_commit_sha":"b"*40,
         "basis_head":"a"*40,"comment_id":42,
         "implementation_event_at":"2026-10-08T09:01:00Z"}
COMMENT = {"id":42,"user":{"id":313684924},"created_at":"2026-10-08T09:00:00Z",
           "updated_at":"2026-10-08T09:00:00Z",
           "body":"CB6-APPROVE change-A " + DIGEST + " " + "b"*40}
DATA = {"proposed_change_id":"change-A","basis_head":"a"*40,
        "approval":{"approval_id":"A-1","approved_at":"2026-10-08T09:00:00Z",
                    "proposed_change_id":"change-A","approved_change_summary":"exact change A",
                    "github_reference":"issue-comment:42"}}

class TestApproval(unittest.TestCase):
    def test_ac01_to_ac12_and_dt01_to_dt12(self):
        self.assertEqual(v.check(DATA, COMMENT, TRUST), [])
        mutations = [
            lambda d,c,t: c["user"].update(id=1),
            lambda d,c,t: d.update(proposed_change_id="change-B"),
            lambda d,c,t: t.update(plan_sha256="0"*64),
            lambda d,c,t: t.update(basis_head="c"*40),
            lambda d,c,t: t["plan"]["planned_paths"].append("unapproved"),
            lambda d,c,t: t.update(implementation_event_at="2026-10-08T08:59:00Z"),
            lambda d,c,t: d["approval"].update(approved_at="2026-10-08T08:59:00Z"),
            lambda d,c,t: c.update(updated_at="2026-10-08T09:02:00Z"),
            lambda d,c,t: c.clear(),
            lambda d,c,t: t.pop("plan"),
            lambda d,c,t: d["approval"].pop("github_reference"),
            lambda d,c,t: d.update(approval=None),
        ]
        for n, change in enumerate(mutations, 1):
            d,c,t = copy.deepcopy((DATA, COMMENT, TRUST))
            change(d,c,t)
            with self.subTest(DT=n):
                self.assertTrue(v.check(d,c,t), "DT-%02d accepted" % n)
        print("AC-01..12 / DT-01..12: PASS (synthetic only)")

    def test_live_api_failure_and_mock_separation(self):
        t = dict(TRUST, repository="kan1975-creator/CB6-Navi-Public-Build",
                 plan_path="approval-plan.json")
        def broken(*args):
            raise OSError("offline")
        self.assertTrue(v.verify_live(DATA,t,"test-token",fetch=broken))
        self.assertTrue(v.check(DATA))
        self.assertEqual(v.main(["verifier"]),1)

if __name__ == "__main__":
    unittest.main()
