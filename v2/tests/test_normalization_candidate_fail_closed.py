#!/usr/bin/env python3
"""Candidate destructive tests: audit errors vs release blockers and PR trigger."""
import copy
import importlib.util
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "gates/verify_normalization_candidate.py"
spec = importlib.util.spec_from_file_location("candidate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
h, b = "a"*40, "b"*40
base = {"pr":{"head":{"sha":h},"base":{"sha":b},"state":"open","draft":True,"user":{"login":"author"}},
        "files":[{"filename":x,"status":"added"} for x in sorted(m.ALLOWED)],
        "review_threads":[],
        "reviews":[{"state":"APPROVED","commit_id":h,"user":{"login":"independent"}}],
        "runs":[{"name":n,"head_sha":h,"status":"completed","conclusion":"success"} for n in m.REQUIRED_CHECKS],
        "branch":{"protected":True,"commit":{"sha":b}}}
errors, blockers = m.audit(base,h,b)
assert not errors and any("approval authenticity" in x for x in blockers)
assert not any("device acceptance" in x for x in blockers)
assert any("independent normalization workflow" in x for x in blockers)
assert not any("review-thread" in x for x in blockers)
cases = [
 ("out-of-scope",lambda x:x["files"].append({"filename":"v2/signals/x","status":"added"}),"error","diff outside"),
 ("stale PR",lambda x:x["pr"]["head"].update(sha="c"*40),"error","HEAD"),
 ("stale base",lambda x:x["branch"]["commit"].update(sha="c"*40),"error","HEAD"),
 ("unresolved thread",lambda x:x.update(review_threads=[{"isResolved":False}]),"block","unresolved review threads"),
 ("missing thread evidence",lambda x:x.pop("review_threads"),"block","review-thread resolution"),
 ("malformed thread evidence",lambda x:x.update(review_threads=[{"isResolved":"yes"}]),"error","malformed review-thread"),
 ("missing independent workflow",lambda x:x.update(runs=[]),"block","independent normalization workflow"),
 ("application scope",lambda x:x["files"].append({"filename":"app/src/main/java/Changed.java","status":"added"}),"block","device acceptance"),
 ("missing review",lambda x:x.update(reviews=[]),"block","review missing"),
 ("self review",lambda x:x["reviews"][0]["user"].update(login="author"),"block","review missing"),
 ("stale review",lambda x:x["reviews"][0].update(commit_id="c"*40),"block","review missing"),
 ("withdrawn approval",lambda x:x["reviews"].append({"state":"DISMISSED","commit_id":h,"user":{"login":"independent"}}),"block","review missing"),
 ("latest changes requested",lambda x:x["reviews"].append({"state":"CHANGES_REQUESTED","commit_id":h,"user":{"login":"independent"}}),"block","unresolved changes"),
 ("other reviewer changes requested",lambda x:x["reviews"].append({"state":"CHANGES_REQUESTED","commit_id":h,"user":{"login":"other"}}),"block","unresolved changes"),
 ("missing CI",lambda x:x.update(runs=[]),"block","current-SHA CI"),
 ("stale CI",lambda x:x["runs"][0].update(head_sha="c"*40),"block","current-SHA CI"),
 ("failed CI",lambda x:x["runs"][0].update(conclusion="failure"),"block","current-SHA CI"),
 ("unprotected",lambda x:x["branch"].update(protected=False),"block","branch protection"),
 ("not draft",lambda x:x["pr"].update(draft=False),"block","draft"),
 ("wrong file status",lambda x:x["files"][0].update(status="removed"),"error","diff outside"),
 ("missing API evidence",lambda x:x.update(files=None),"error","missing GitHub API"),
 ("malformed review",lambda x:x["reviews"].append(None),"error","malformed review"),
]
for name, mutate, kind, needle in cases:
    data=copy.deepcopy(base)
    mutate(data)
    errors, blockers = m.audit(data,h,b)
    target = errors if kind == "error" else blockers
    assert any(needle in s for s in target), name
assert m.audit(None,h,b)[0] == ["malformed GitHub evidence"]
# CLI must not convert malformed input into a successful advisory audit.
assert m.main() == 2
print("PASS: 23 destructive cases; AUDIT_ERROR fails, release blockers remain explicit")

# Regression: candidate reconstruction must run from PR events without a
# workflow_dispatch entry that is unavailable until default-branch installation.
workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/cb6_normalization_candidate.yml").read_text()
assert "  workflow_dispatch:" not in workflow
assert "  pull_request:" in workflow
assert "  independent-review-candidate:" in workflow
assert "if: github.event_name == 'pull_request'" in workflow
assert "fetch-depth: 0" in workflow
assert "RELEASE_BLOCKED: same-workflow job does not establish independent review" in workflow
print("PASS: PR-triggered reconstruction contract; no false independent acceptance")
