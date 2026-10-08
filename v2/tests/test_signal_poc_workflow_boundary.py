#!/usr/bin/env python3
"""Adversarial scope/coverage/HEAD tests for the one-workflow exception."""
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
for token in m.REQUIRED:
    rejects(m.POC_WORKFLOW, workflow.replace(token, "REMOVED", 1), "missing "+token)
rejects(m.POC_WORKFLOW, workflow.replace('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', 'echo "$GITHUB_SHA"', 1), "HEAD check missing")
rejects(m.POC_WORKFLOW, workflow.replace("          python3 v2/baseline/apply_identity.py comaps", "          python3 v2/baseline/apply_identity.py comaps\n          test \"$(git rev-parse HEAD)\" = \"$GITHUB_SHA\"", 1).replace('          test "$(git rev-parse HEAD)" = "$GITHUB_SHA"\n', "", 1), "late HEAD check")
rejects(m.POC_WORKFLOW, workflow+"\nGITHUB_SHA: forged\n", "HEAD override")
print("PASS PoC-only boundary destructive tests")
