#!/usr/bin/env python3
"""Fail-closed adversarial cases for the PoC direct checker."""
import importlib.util
from pathlib import Path
p = Path(__file__).with_name("verify_signal_standard_poc_direct.py")
spec = importlib.util.spec_from_file_location("poc_direct", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def rejected(fn, label):
    try:
        fn()
    except ValueError:
        print("PASS rejected", label)
        return
    raise SystemExit("FAIL accepted " + label)

m.validate_diff(["android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"])
for case in (
    [],
    ["libs/routing/route.cpp"],
    ["libs/search/search.cpp"],
    ["android/app/src/main/java/app/organicmaps/bookmarks/Bookmark.java"],
    ["data/styles/default/light/mdpi/cb6-seven.png"],
    ["v2/gates/verify_project_gate.py"],
):
    rejected(lambda case=case: m.validate_diff(case), repr(case))
rejected(lambda: m.require(False, "stale HEAD"), "stale HEAD")
rejected(lambda: m.require(False, "wrong pinned upstream"), "wrong upstream")
rejected(lambda: m.require(False, "missing Signal JNI"), "missing integration")
rejected(lambda: m.require(False, "diagnostic contamination"), "diagnostic contamination")
print("PASS PoC direct verifier adversarial unit tests")
