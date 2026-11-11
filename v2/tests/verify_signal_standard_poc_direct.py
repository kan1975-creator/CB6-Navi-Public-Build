#!/usr/bin/env python3
"""PoC-only direct product checks. Does not certify approval or device acceptance."""
import argparse
import os
import subprocess
from pathlib import Path

PINNED_COMAPS = "7113ccb5f086183f8884b2aa4e58c987466b6704"
ALLOWED_PREFIXES = ("android/", "libs/map/", "libs/storage/", "data/styles/default/")
ALLOWED_EXACT = {"libs/platform/http_request.cpp", "data/styles/vehicle/include/Icons.mapcss"}
PROTECTED = ("libs/routing/", "libs/search/", "android/app/src/main/java/app/organicmaps/search/",
             "android/app/src/main/java/app/organicmaps/bookmarks/",
             "android/app/src/main/java/app/organicmaps/downloader/")
BRANDS = ("cb6-seven", "cb6-familymart", "cb6-lawson", "cb6-seicomart", "cb6-ministop", "cb6-mybasket")

def allowed(path):
    return (path.startswith(ALLOWED_PREFIXES) or path in ALLOWED_EXACT or
            (path.startswith("data/styles/") and path.endswith("/include/priorities_4_overlays.prio.txt")))

def validate_diff(paths):
    if not paths:
        raise ValueError("empty generated diff")
    for path in paths:
        if not allowed(path) or path.startswith(PROTECTED) or any(b in path for b in BRANDS):
            raise ValueError("out-of-scope generated change: " + path)

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def run(args, cwd):
    subprocess.run(args, cwd=cwd, check=True)

def output(args, cwd):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()

def verify(root, tree):
    require(tree.is_dir(), "missing CoMaps tree")
    expected = os.environ.get("GITHUB_SHA")
    if expected:
        require(output(["git", "rev-parse", "HEAD"], root) == expected, "checkout/GITHUB_SHA mismatch")
    require(output(["git", "rev-parse", "HEAD"], tree) == PINNED_COMAPS, "upstream SHA mismatch")
    paths = output(["git", "diff", "--name-only"], tree).splitlines()
    validate_diff(paths)
    fw = (tree / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp").read_text()
    sig = (tree / "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc").read_text()
    mwm = (tree / "android/app/src/main/java/app/organicmaps/MwmActivity.java").read_text()
    require('#include "cb6_signal_jni.inc"' in fw and "nativeSetCb6Signals" in sig and
            "mCb6Signals" in mwm, "Signal JNI/lifecycle integration missing")
    require("nativeCb6CollectConvenienceMarks" not in fw and
            "nativeSetCb6ConvenienceMarks" not in fw, "unexpected Convenience integration")
    require("nativeCb6ConvenienceDiagnostic" not in fw and
            "CB6-CONVENIENCE-ZOOM-DIAG" not in mwm, "diagnostic path in production")
    run(["git", "diff", "--check"], tree)
    checks = [
        ["python3", "v2/audits/preflight_gate1.py", str(tree), "out/GENERATED_SOURCE_SHA256.json", "--verify"],
        ["python3", "v2/audits/audit_identity.py", str(tree)],
        ["python3", "v2/audits/audit_signals.py", str(tree), "--atlases"],
        ["python3", "v2/tests/signals_audit_selftest.py", str(tree)],
    ]
    for cmd in checks:
        run(cmd, root)
    print("PASS PoC direct Signal checks; device acceptance and approval not certified")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tree", default="comaps")
    a = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        verify(root, (root / a.tree).resolve())
    except (ValueError, subprocess.CalledProcessError, OSError) as exc:
        raise SystemExit("FAIL PoC direct checks: " + str(exc))

if __name__ == "__main__":
    main()
