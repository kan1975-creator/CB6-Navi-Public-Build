# CB6 Governance Normalization — candidate phase 1

Status: CANDIDATE, not ACTIVE. No legacy rule or gate is superseded.

## Authority and scope
- The latest GitHub repository HEAD and ACTIVE contracts are authoritative. Chat memory is not.
- Only these four new candidate files are authorized for phase 1. No app, Signal, Convenience, legacy Gate, Method Freeze, or PR #3 changes.
- This candidate is advisory and fail-closed. A PASS of its local tests is **not** an authorization to implement, merge, retire a gate, or claim device acceptance.

## Workflow
User requirements and acceptance criteria -> reconstruct HEAD and applicable rules -> multi-angle read-only research and impact assessment -> specific prior approval -> implementation within approved scope -> PR and direct tests -> independent review -> APK provenance -> CB6 device acceptance -> merge decision.

## AC-01..AC-12
01 HEAD freshness; 02 authentic, prior, change-bound approval; 03 actual PR diff within approved paths; 04 evidence-backed multi-angle research; 05 ACTIVE rules/spec consistency; 06 direct tests cannot be skipped; 07 independent review with blocking findings resolved; 08 checks tied to target SHA; 09 APK source/signature/hash; 10 real device acceptance before completion; 11 applicability to current/future work; 12 old gate remains in force until equivalent destructive tests and explicit retirement approval.

## Evidence policy
The verifier can check declared evidence consistency, but **cannot establish approval authenticity from self-declared JSON**. Approval remains BLOCKED until a trusted user-authorized source and binding procedure is independently established. A GitHub PR description alone is not proof of user approval. Likewise self-declared test/review results are not authoritative. GitHub PR files and commit status must be fetched live before a release decision.

## Transition guardrails
The standard branch was observed as unprotected. Candidate PASS cannot substitute for verified required checks/branch protection. If protection, real independent review, APK provenance or device acceptance is missing, release/retirement remains BLOCKED. No automatic approval, auto-merge, or scheduled monitoring.
