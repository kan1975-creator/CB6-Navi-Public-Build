# CB6 Governance Normalization — candidate phase 2

Status: CANDIDATE, not ACTIVE. Existing Development Gate and ACTIVE rules remain authoritative.

## Scope and workflow
Only these four candidate files may be modified in phase 2. No Signal, Convenience, app runtime, Method Freeze, PR #3, or legacy gate changes. Follow fresh HEAD -> research -> prior explicit user approval -> scoped PR -> real tests -> independent review -> APK provenance -> actual device acceptance.

## AC-01–AC-12
01 HEAD freshness; 02 authentic prior approval; 03 actual PR diff scope; 04 multi-angle research; 05 ACTIVE spec consistency; 06 direct tests; 07 independent review; 08 same-SHA CI; 09 APK provenance/signature/hash; 10 real device Acceptance; 11 future-feature coverage; 12 no legacy gate retirement before equivalence and explicit adoption.

## Phase 2 evidence policy
The workflow uses read-only GitHub REST API to retrieve actual PR files, PR head/base SHA, current base branch, PR reviews, and Actions runs. The candidate audit checks actual diff against the four allowed files, independently authored GitHub review on current SHA, and required CI names with successful runs on PR head SHA. It rejects incomplete pagination and API errors. API-shaped destructive tests cover stale SHA, scope drift, missing/failed CI, absent/self/stale review, malformed evidence and unprotected branch.

**Important:** A passing candidate job only means the audit executed and blockers were reported; it is NOT a successful authorization decision. A GitHub API token cannot authenticate user approval given in ChatGPT. The candidate therefore always reports user-approval authenticity as BLOCKED. APK/device Acceptance likewise remains BLOCKED. GitHub branch protection is separately checked, not configured. No automated merge or monitoring.

The pull_request event checks out GitHub's synthetic merge SHA; the audit separately compares the PR head SHA to CI run head SHA. Existing Development Gate must remain successful. Release, formal adoption and old gate retirement require separate explicit approval and real evidence.
