# CB6 Governance Normalization — candidate phase 3

Status: CANDIDATE, not ACTIVE. Existing Development Gate and ACTIVE rules remain authoritative.

## Scope
Only these four candidate files may be modified. No legacy Gate, Method Freeze, ACTIVE rules, PR #3, Signal, Convenience or app runtime changes.

## AC-01–AC-12
01 HEAD freshness; 02 authentic prior approval; 03 actual PR diff scope; 04 multi-angle research; 05 ACTIVE consistency; 06 direct tests; 07 independent review; 08 same-SHA CI; 09 APK provenance; 10 real device Acceptance; 11 future-feature coverage; 12 legacy gate preservation.

## Phase 3 audit semantics
- AUDIT_ERROR: malformed/missing GitHub API evidence, HEAD mismatch or out-of-scope PR diff. Nonzero exit, candidate CI fails.
- AUDIT_OK: read-only evidence inspection completed without audit errors. Zero exit means only this, never approval.
- RELEASE_BLOCKED: independent release prerequisites absent. Always reported, not silently converted into an approval.
- Candidate workflow must not depend on its own completion. Only existing Development Gate is inspected for same-head SHA success.
- GitHub review evidence is evaluated using the latest decisive review state per independent reviewer; dismissed/stale approvals cannot authorize. CHANGES_REQUESTED is blocking. Review-thread resolution is not yet checked and therefore remains explicitly blocked.
- User approval in ChatGPT cannot be independently authenticated by GitHub API. APK/device acceptance and branch protection are separate, unresolved release prerequisites.
- Pull request checkout uses synthetic merge SHA; audit separately checks PR head SHA. API failures and pagination truncation are audit errors.

## Transition guardrails
A candidate CI SUCCESS is never authorization to merge, retire old gates or mark app/device acceptance. PR #4 stays Draft and unmerged. Independent review and explicit user approval are mandatory before any ACTIVE change. No auto-merge or monitoring.
