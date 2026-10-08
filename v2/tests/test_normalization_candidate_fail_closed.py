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
assert not errors and any("ACTIVE pre-fix approval" in x for x in blockers)
assert not any("device acceptance" in x for x in blockers)
assert any("ACTIVE independent review" in x for x in blockers)
assert not any("review-thread" in x for x in blockers)
cases = [
 ("out-of-scope",lambda x:x["files"].append({"filename":"v2/signals/x","status":"added"}),"error","diff outside"),
 ("stale PR",lambda x:x["pr"]["head"].update(sha="c"*40),"error","HEAD"),
 ("stale base",lambda x:x["branch"]["commit"].update(sha="c"*40),"error","HEAD"),
 ("unresolved thread",lambda x:x.update(review_threads=[{"isResolved":False}]),"block","unresolved review threads"),
 ("missing thread evidence",lambda x:x.pop("review_threads"),"block","review-thread resolution"),
 ("malformed thread evidence",lambda x:x.update(review_threads=[{"isResolved":"yes"}]),"error","malformed review-thread"),
 ("missing independent workflow",lambda x:x.update(runs=[]),"block","ACTIVE independent review"),
 ("application scope",lambda x:x["files"].append({"filename":"app/src/main/java/Changed.java","status":"added"}),"block","device acceptance"),
 ("missing review",lambda x:x.update(reviews=[]),"block","ACTIVE independent review"),
 ("self review",lambda x:x["reviews"][0]["user"].update(login="author"),"block","ACTIVE independent review"),
 ("stale review",lambda x:x["reviews"][0].update(commit_id="c"*40),"block","ACTIVE independent review"),
 ("withdrawn approval",lambda x:x["reviews"].append({"state":"DISMISSED","commit_id":h,"user":{"login":"independent"}}),"block","ACTIVE independent review"),
 ("latest changes requested",lambda x:x["reviews"].append({"state":"CHANGES_REQUESTED","commit_id":h,"user":{"login":"independent"}}),"block","unresolved changes"),
 ("other reviewer changes requested",lambda x:x["reviews"].append({"state":"CHANGES_REQUESTED","commit_id":h,"user":{"login":"other"}}),"block","unresolved changes"),
 ("missing CI",lambda x:x.update(runs=[]),"block","current-SHA CI"),
 ("stale CI",lambda x:x["runs"][0].update(head_sha="c"*40),"block","current-SHA CI"),
 ("failed CI",lambda x:x["runs"][0].update(conclusion="failure"),"block","current-SHA CI"),
 ("unprotected",lambda x:x["branch"].update(protected=False),"block","ACTIVE independent review"),
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
print("PASS: destructive cases; AUDIT_ERROR fails, ACTIVE review and approval remain blocked")

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

# Candidate-only GitHub reviewer, named workflow and branch protection cannot
# stand in for ACTIVE independent review or ACTIVE pre-fix approval.
for mutation in (
    lambda x:x["reviews"].clear(),
    lambda x:x["branch"].update(protected=False),
    lambda x:x["runs"].append({"name":"CB6 Governance Normalization Independent Review","head_sha":h,"status":"completed","conclusion":"success"}),
):
    data=copy.deepcopy(base); mutation(data)
    err, blocked=m.audit(data,h,b)
    assert not err
    assert any("ACTIVE independent review" in x for x in blocked)
    assert any("ACTIVE pre-fix approval" in x for x in blocked)
print("PASS: independent review and pre-fix approval cannot be spoofed by GitHub candidate metadata")

# Evidence-specific destructive tests: no candidate-local assertion can
# substitute for a GitHub-authenticated, current-SHA independent attestation.
good=copy.deepcopy(base)
good["pr"]["body"]="approval-ref-123"
good["approval_evidence"]={
    "approval_id":"a1","approved_at":"2026-10-01T00:00:00Z",
    "implementation_started_at":"2026-10-02T00:00:00Z",
    "proposed_change_id":"change-1","change_id":"change-1",
    "approved_change_summary":"candidate normalization",
    "github_reference":"approval-ref-123",
    "authenticated_by":"independent_external_verification"}
good["independent_review_evidence"]={
    "target_commit":h,"implementation_context_shared":False,
    "result":"ACCEPTED","checklist":"v2/governance/audit_checklist_v1.md",
    "evidence":["github evidence"],"review_context":"separate session",
    "verified_external_provenance":True}
# The GitHub review body is the independently fetched attestation.
good["reviews"][0]["body"]="CB6-INDEPENDENT-CONTEXT:"+h
e,k=m.audit(good,h,b)
assert not e and not k,(e,k)
for name,mutate,needle in [
 ("stale independent target",lambda x:x["independent_review_evidence"].update(target_commit="c"*40),"invalid or stale"),
 ("shared review context",lambda x:x["independent_review_evidence"].update(implementation_context_shared=True),"invalid or stale"),
 ("empty independent evidence",lambda x:x["independent_review_evidence"].update(evidence=[]),"invalid or stale"),
 ("review rejected",lambda x:x["independent_review_evidence"].update(result="REJECTED"),"invalid or stale"),
 ("spoofed external review",lambda x:x["reviews"][0].update(body="self-assertion"),"external attestation"),
 ("stale GitHub review",lambda x:x["reviews"][0].update(commit_id="c"*40),"external attestation"),
 ("unverified reviewer provenance",lambda x:x["independent_review_evidence"].update(verified_external_provenance=False),"separation"),
 ("approval reuse",lambda x:x["approval_evidence"].update(change_id="different"),"binding or timing"),
 ("post-hoc approval",lambda x:x["approval_evidence"].update(approved_at="2026-10-03T00:00:00Z"),"binding or timing"),
 ("missing approval reference",lambda x:x["pr"].update(body=""),"binding or timing"),
 ("unauthenticated approval",lambda x:x["approval_evidence"].update(authenticated_by="self"),"authenticity"),
]:
    data=copy.deepcopy(good);mutate(data)
    errors,blocks=m.audit(data,h,b)
    assert any(needle in x for x in blocks),name+":"+str((errors,blocks))
print("PASS: valid evidence unlocks candidate blockers; 11 evidence mutations fail closed")
