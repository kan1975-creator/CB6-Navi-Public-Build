#!/usr/bin/env python3
"""Destructive candidate tests: no false authorization from self-declared evidence."""
import copy
import importlib.util
import pathlib
import tempfile
import json

root = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("candidate", root / "v2/gates/verify_normalization_candidate.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sha = "a" * 40
ok = {"basis_head":sha, "target_head":sha, "change_id":"C1",
      "planned_paths":["docs/a"], "actual_pr_paths":["docs/a"],
      "approval":{"change_id":"C1", "basis_head":sha, "approved_at":"2026-10-08"},
      "research":{"verified":True,"evidence_refs":["research"]},
      "tests":{"verified":True,"evidence_refs":["test"]},
      "review":{"verified":True,"evidence_refs":["review"]},
      "checks":{"verified":True,"evidence_refs":["checks"],"head_sha":sha},
      "apk":{"verified":True,"evidence_refs":["apk"]},
      "device":{"verified":True,"evidence_refs":["device"]},
      "branch_protection":True, "completion":True}
assert any("approval authenticity" in x for x in mod.validate(ok)), "self-approval incorrectly accepted"
cases = [
 ("missing approval", lambda d:d.pop("approval"), "missing approval"),
 ("reused approval", lambda d:d["approval"].update(change_id="C2"), "approval binding mismatch"),
 ("scope drift", lambda d:d["actual_pr_paths"].append("v2/signals/forbidden"), "outside approved"),
 ("stale CI", lambda d:d["checks"].update(head_sha="b"*40), "CI HEAD mismatch"),
 ("missing research", lambda d:d["research"].update(verified=False), "research missing"),
 ("skipped tests", lambda d:d["tests"].update(verified=False), "tests missing"),
 ("missing review", lambda d:d["review"].update(verified=False), "review missing"),
 ("APK missing", lambda d:d["apk"].update(verified=False), "apk missing"),
 ("device missing", lambda d:d["device"].update(verified=False), "device missing"),
 ("unprotected branch", lambda d:d.update(branch_protection=False), "branch protection"),
]
for label, change, expected in cases:
    d = copy.deepcopy(ok)
    change(d)
    assert any(expected in err for err in mod.validate(d)), label
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t)/"self_declared.json"
    p.write_text(json.dumps(ok),encoding="utf-8")
    assert mod.main(["candidate",str(p)]) != 0
    assert mod.main(["candidate",str(p.parent/"missing.json")]) != 0
print("PASS: 10 destructive cases; self-declared approval and missing evidence fail closed")
