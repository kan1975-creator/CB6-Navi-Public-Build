# CB6 Continuing Work Notes

Purpose: durable restart/index notes for CB6 work. This file is informational working context, not an Operational Rule Registry contract, verifier, Coverage authority, Method Freeze authority, or substitute for ACTIVE GitHub authority. If this note conflicts with current ACTIVE authority, current ACTIVE authority wins.

## Restart authority checklist

At CB6 work/session restart, use current GitHub state rather than chat memory. Reconstruct the current state from the latest branch HEAD and the applicable repository authorities, including:

- `v2/gates/cb6_master_progress.json` for the repository progress entrypoint/index.
- `v2/gates/active_decisions.json` and `v2/gates/current_spec.json` for active product decisions/specification.
- the current ACTIVE Operational Rule Registry and its referenced contracts.
- `v2/governance/status_reporting_protocol.md` / current ACTIVE Status Reporting contract for progress-report behavior.
- the current development-method authority and applicable feature evidence.

Do not copy ACTIVE rule text into this note as a competing authority.

## Existing ACTIVE authority — reference, do not duplicate

The following are already governed by current ACTIVE authority and must be read from that authority rather than redefined here:

- progress classifications, report-start tags and final four-line format;
- wait-time/run-start/cumulative elapsed/next-check behavior;
- direct refresh of a known tracked Actions Run ID;
- concrete smartphone-operation/evidence instructions;
- implementation-problem fix approval boundary;
- acceptance criteria, read-only investigation, cause analysis and avoidance of unnecessary diagnostics;
- rule-consistency preflight before creating or revising continuing rules.

## Continuing working notes not promoted to new governance here

These notes preserve current user-agreed operating context without claiming new machine-enforced ACTIVE rules:

1. Prefer broad read-only investigation first. Use an analysis/diagnostic-only APK as a last observational tool when multi-angle read-only investigation still cannot establish the required cause/value with sufficient certainty.
2. For the current development phase, do not run parallel feature implementations. Keep one implementation target active at a time; non-conflicting read-only investigation is distinct from parallel implementation.
3. When ChatGPT fails to apply an existing rule correctly, first treat it as an execution/application failure and check whether existing authority already covered the situation. Do not automatically conclude that a new governance rule is required.
4. Do not interrupt feature development merely to improve governance that is currently passing. Propose governance change only when a concrete gap not adequately covered by existing authority is demonstrated, and follow the existing rule-consistency/adoption process if such a change is actually needed.
5. Do not reopen settled decisions without new conflicting evidence, a changed requirement, or a verified authority conflict.
6. When an APK is ready for user/device work, provide a direct download route/link to the relevant APK/Artifact when technically available, alongside the build identity required by ACTIVE evidence rules.
7. When a confirmed product specification changes, keep the atomic requirement list and the product specification/decision authorities consistent with that change. Reuse the existing atomic/specification system rather than creating a competing specification list in this note.
8. Specification-list synchronization must not obstruct application development. Perform the synchronization as a small accompanying maintenance task when practical; if it is non-conflicting and tooling permits, progress it in parallel/background while the primary application-development target continues. Do not delay or stop application development solely to polish or comprehensively reorganize the lists unless a concrete authority/traceability conflict makes the application change unsafe.

## Historical note

`v2/governance/session_summary_2026-09-30.md` remains a dated historical handoff. Do not treat its then-current feature priority as current merely because it is recorded there.
