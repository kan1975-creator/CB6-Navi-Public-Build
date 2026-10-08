#!/usr/bin/env python3
"""Adversarial tests for the Signal PoC workflow boundary."""
import importlib.util
from pathlib import Path
root = Path(__file__).resolve().parents[2]
p = root / "v2/gates/signal_poc_workflow_boundary.py"
spec = importlib.util.spec_from_file_location("poc_boundary", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
workflow = (root / ".github/workflows" / m.POC_WORKFLOW).read_text()
assert m.validate_poc_workflow(m.POC_WORKFLOW, workflow)
def rejects(name, source, label):
    try:
        m.validate_poc_workflow(name, source)
    except ValueError:
        print("PASS rejected", label)
        return
    raise SystemExit("FAIL accepted " + label)
rejects("build_other_workflow.yml", workflow, "exception expansion")
for token in m.REQUIRED + m.PATHS:
    rejects(m.POC_WORKFLOW, workflow.replace(token, "REMOVED"), "missing " + token)
rejects(m.POC_WORKFLOW, workflow.replace('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', 'echo "$GITHUB_SHA"'), "HEAD check missing")
rejects(m.POC_WORKFLOW, workflow + "\nGITHUB_SHA: forged\n", "HEAD override")
rejects(m.POC_WORKFLOW, workflow.replace("      - name: Executable APK Build Preflight\n", "      - name: Executable APK Build Preflight\n        if: false\n"), "skipped direct check")
rejects(m.POC_WORKFLOW, workflow.replace("      - name: Verify Gate 1 APK\n", "      - name: Verify Gate 1 APK\n        continue-on-error: true\n"), "ignored APK failure")
rejects(m.POC_WORKFLOW, workflow.replace("          python3 v2/tests/test_signal_standard_poc_direct.py", "          # python3 v2/tests/test_signal_standard_poc_direct.py"), "commented direct test")
rejects(m.POC_WORKFLOW, workflow.replace('          grep -Fx "commit=$GITHUB_SHA" out/BUILD_PROVENANCE.txt', '          echo "commit=$GITHUB_SHA"'), "unbound provenance")
rejects(m.POC_WORKFLOW, workflow.replace("        if: success()\n        uses: actions/upload-artifact@v4", "        if: always()\n        uses: actions/upload-artifact@v4"), "upload after failure")
print("PASS PoC-only boundary destructive tests")
