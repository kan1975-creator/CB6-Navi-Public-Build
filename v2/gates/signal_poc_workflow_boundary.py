"""Fail-closed workflow-specific direct checks; no production exception expansion."""
import re
POC_WORKFLOW = "build_cb6_v2_signals_standard_poc.yml"
REQUIRED = (
    "python3 v2/tests/test_signal_standard_poc_direct.py",
    "python3 v2/tests/verify_signal_standard_poc_direct.py --tree comaps",
    'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
    "python3 v2/audits/preflight_gate1.py comaps",
    "python3 v2/audits/audit_signals.py comaps",
    "python3 v2/tests/signals_audit_selftest.py comaps",
    "git -C comaps diff --check",
    "app:assembleWebRelease", "audit_signals.py comaps --apk",
    "apksigner", "sha256sum", "actions/upload-artifact@v4",
)
PATHS = ("'v2/**'", "'scripts/**'", "'CB6_*.py'", "'validate_package.py'")
def validate_poc_workflow(name, source):
    if name != POC_WORKFLOW:
        raise ValueError("not the approved PoC workflow")
    for token in REQUIRED + PATHS:
        if token not in source:
            raise ValueError("missing PoC requirement: " + token)
    if any(line.strip().startswith(("GITHUB_SHA:", "GITHUB_SHA=")) for line in source.splitlines()) or "unset GITHUB_SHA" in source:
        raise ValueError("GITHUB_SHA override")
    if "  pull_request:\\n    branches:\\n      - cb6-v2-clean\\n    paths:" not in source:
        raise ValueError("missing scoped PR trigger")
    blocks = re.split(r"(?m)^      - name: ", source)
    if len(blocks) < 3:
        raise ValueError("no executable steps")
    steps = {}
    for block in blocks[1:]:
        name, _, body = block.partition("\\n")
        if name in steps:
            raise ValueError("duplicate step")
        steps[name] = body
        if name != "Upload Signal PoC failure evidence" and name != "Upload verified Signal PoC APK and direct evidence":
            if re.search(r"(?m)^        (if:|continue-on-error:)", body):
                raise ValueError("skippable step")
        if "run: |" in body and not re.search(r"(?m)^          set -euxo pipefail$", body):
            raise ValueError("non-fail-closed step")
    order = list(steps)
    critical = ["Preflight control repository", "Apply consolidated identity and signal modules", "Final generated source and every atlas audit", "Executable APK Build Preflight", "Build CB6 Gate 1 arm64 release", "Verify Gate 1 APK", "Upload verified Signal PoC APK and direct evidence"]
    if any(n not in steps for n in critical) or [order.index(n) for n in critical] != sorted(order.index(n) for n in critical):
        raise ValueError("required steps absent or unordered")
    pre = steps[critical[0]]
    for token in ('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', 'out/BUILD_PROVENANCE.txt', 'GITHUB_EVENT_PATH', 'merge_commit_sha'):
        if token not in pre:
            raise ValueError("missing provenance check")
    direct = steps["Executable APK Build Preflight"]
    for token in REQUIRED[:2]:
        if not re.search(r"(?m)^          " + re.escape(token) + r"$", direct):
            raise ValueError("direct check not executable")
    verify = steps["Verify Gate 1 APK"]
    for token in ('sha256sum out/CB6-V2-Gate1-Signals-arm64.apk', 'grep -Fx "commit=$GITHUB_SHA" out/BUILD_PROVENANCE.txt', 'test -s out/SHA256SUMS.txt'):
        if token not in verify:
            raise ValueError("artifact provenance missing")
    upload = steps["Upload verified Signal PoC APK and direct evidence"]
    if "if: success()" not in upload or "out/*.apk" not in upload or "out/*.txt" not in upload:
        raise ValueError("artifact upload not success-bound")
    return True
