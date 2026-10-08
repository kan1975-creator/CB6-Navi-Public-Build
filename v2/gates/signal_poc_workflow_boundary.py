"""Narrow, fail-closed exemption for the Signal standard-flow PoC only."""
POC_WORKFLOW = "build_cb6_v2_signals_standard_poc.yml"
REQUIRED = (
    "python3 v2/tests/test_signal_standard_poc_direct.py",
    "python3 v2/tests/verify_signal_standard_poc_direct.py --tree comaps",
    'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
    "python3 v2/audits/preflight_gate1.py comaps",
    "python3 v2/audits/audit_signals.py comaps",
    "python3 v2/tests/signals_audit_selftest.py comaps",
    "git -C comaps diff --check",
    "app:assembleWebRelease",
    "audit_signals.py comaps --apk",
    "apksigner",
    "sha256sum",
    "actions/upload-artifact@v4",
)
def validate_poc_workflow(name, source):
    if name != POC_WORKFLOW:
        raise ValueError("not the approved PoC workflow")
    for token in REQUIRED:
        if token not in source:
            raise ValueError("missing PoC direct check: " + token)
    if any(line.strip().startswith(("GITHUB_SHA:", "GITHUB_SHA=")) for line in source.splitlines()) or "unset GITHUB_SHA" in source:
        raise ValueError("GITHUB_SHA override")
    head = source.index('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"')
    transform = min(source.index("python3 v2/baseline/apply_identity.py"), source.index("python3 v2/signals/apply_signals.py"))
    if head > transform:
        raise ValueError("HEAD check occurs after source transform")
    direct = source.index("python3 v2/tests/verify_signal_standard_poc_direct.py --tree comaps")
    build = source.index("app:assembleWebRelease")
    if direct > build:
        raise ValueError("direct checks occur after APK build")
    return True
