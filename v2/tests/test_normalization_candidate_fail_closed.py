#!/usr/bin/env python3
"""GitHub evidence audit destructive tests, using isolated API-shaped fixtures."""
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
        "reviews":[{"state":"APPROVED","commit_id":h,"user":{"login":"independent"}}],
        "runs":[{"name":n,"head_sha":h,"status":"completed","conclusion":"success"} for n in m.REQUIRED_CHECKS],
        "branch":{"protected":True,"commit":{"sha":b}}}
assert any("approval authenticity" in x for x in m.audit(base,h,b))
assert any("device acceptance" in x for x in m.audit(base,h,b))
cases = [
 ("out-of-scope",lambda x:x["files"].append({"filename":"v2/signals/x","status":"added"}),"diff outside"),
 ("stale PR",lambda x:x["pr"]["head"].update(sha="c"*40),"HEAD"),
 ("stale base",lambda x:x["branch"]["commit"].update(sha="c"*40),"HEAD"),
 ("missing review",lambda x:x.update(reviews=[]),"review missing"),
 ("self review",lambda x:x["reviews"][0]["user"].update(login="author"),"review missing"),
 ("stale review",lambda x:x["reviews"][0].update(commit_id="c"*40),"review missing"),
 ("missing CI",lambda x:x.update(runs=[]),"current-SHA CI"),
 ("stale CI",lambda x:x["runs"][0].update(head_sha="c"*40),"current-SHA CI"),
 ("failed CI",lambda x:x["runs"][0].update(conclusion="failure"),"current-SHA CI"),
 ("unprotected",lambda x:x["branch"].update(protected=False),"branch protection"),
 ("not draft",lambda x:x["pr"].update(draft=False),"draft"),
 ("wrong status",lambda x:x["files"][0].update(status="removed"),"diff outside"),
 ("missing API evidence",lambda x:x.update(files=None),"missing GitHub API"),
]
for name, mutate, needle in cases:
    data=copy.deepcopy(base)
    mutate(data)
    assert any(needle in s for s in m.audit(data,h,b)), name
assert m.audit(None,h,b) == ["malformed GitHub evidence"]
print("PASS: 14 API-shaped destructive cases; approval/device always blocked")
