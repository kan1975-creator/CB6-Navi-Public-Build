# CB6 Development Execution Gate

Status: ACTIVE EXECUTION ENTRY POINT
Effective: 2026-09-26
Purpose: execute the already-agreed CB6 development policy consistently. This does not replace the policy.

## Why this file exists

CB6 already had the required development policy, internal-analysis records, change-impact rules, frozen/accepted behavior, web/cross-project research and regression rules. Repeated failures occurred because those records were not consistently used as mandatory inputs to the next engineering step. A record that is not consumed by the next step cannot protect the project.

From this point, no CB6 feature implementation or build is authorized merely because a chat says to continue. The repository state below is the entry condition.

## Current project gate

OVERALL DESIGN REBUILD IN PROGRESS.

The previous `CB6_V2_OVERALL_SYSTEM_DESIGN.md` is RETIRED AS CANONICAL. It is historical input only. Feature implementation/build work is paused except work required to inspect evidence, correct the development gate itself, or rebuild/verify the overall design.

## Existing policy that must be executed (not reinvented)

The existing mandatory process in `CB6_KNOWN_FAILURES_AND_PROCESS.md` remains authoritative:
- identify the changed concept/flow, not only the failing line;
- repository-wide search for old references/assumptions;
- inspect implementation/apply scripts/audits/workflows/resources/generated output;
- inspect workflow ordering;
- update affected implementation and validation together;
- preserve accepted/standard CoMaps behavior unless explicitly changed;
- check known failures and regressions;
- inspect final generated source;
- preflight before build;
- never alter correct implementation to satisfy a stale validator;
- APK verification and CB6 real-device behavior remain final authority.

## Mandatory evidence inputs for the rebuilt overall design

The rebuild must actively consume, not merely cite:

1. User-decided CB6 requirements and later explicit changes.
2. CB6 real-device observations and acceptance/rejection history.
3. `CB6_PINNED_COMAPS_INTERNAL_ANALYSIS.md` and any required fresh trace against pinned CoMaps source.
4. Web research already performed and fresh official/upstream research where information may be incomplete or stale.
5. `CB6_V2_CROSS_PROJECT_COMPARISON.md` plus source-backed external OSS findings.
6. `CB6_KNOWN_FAILURES_AND_PROCESS.md`.
7. `CB6_FROZEN_FEATURES.md`, while distinguishing current user changes from obsolete historical freeze details.
8. `CB6_CHANGE_IMPACT_MAP.md`.
9. Existing V2 implementation, successful/failed Actions runs and APK/CB6 evidence as evidence only, not as design authority.
10. The retired overall design, used only for a final omission comparison after rebuilding from the evidence above.

## Evidence-to-design completion requirement

For every planned feature/subsystem, the rebuilt design must show:
- current user requirement;
- relevant pinned-CoMaps facts;
- relevant web/external evidence, or explicit N/A;
- relevant real-device/history evidence, or explicit none;
- known failure/regression constraints;
- selected architecture and why;
- affected modules/interfaces;
- unresolved evidence gates;
- verification/real-device acceptance route.

A subsystem is not design-complete if one of these fields is silently omitted. Unknown remains UNKNOWN/OPEN; it must not be converted into an assumption.

## Execution state machine

Only these transitions are valid:

EVIDENCE -> DESIGN -> IMPACT CHECK -> IMPLEMENTATION -> REPO-WIDE SWEEP -> PREFLIGHT -> BUILD -> APK VERIFY -> CB6 REAL-DEVICE -> ACCEPT/FREEZE

A failed stage returns to the earliest affected stage. It does not skip forward.

For the current rebuild:
EVIDENCE -> REBUILT OVERALL DESIGN -> CROSS-CHECK AGAINST RETIRED DESIGN -> CONSISTENCY REVIEW -> APPROVED DESIGN BASELINE.

Only after that baseline exists may feature implementation resume.

## Persistent anti-regression mechanism

Every development run must read this file first and state the current gate from repository content. The current gate is not inferred from chat memory.

Workflow/build entry points must run a repository preflight that verifies the project gate permits a build. During the overall-design rebuild, ordinary feature workflows are not to be used as a substitute for completing the design gate.

When implementation resumes, each feature must have a machine-readable gate record under `v2/gates/` identifying its design section, affected modules, required audits/tests and current stage. Workflows must reject a missing/invalid gate record. This is the execution mechanism for the existing development policy, not a new product/development policy.

## Change propagation rule

A user decision or new technical finding is not complete when written in one document. The same development cycle must:
1. identify the owning evidence record;
2. identify every downstream design/impact/implementation/audit location affected;
3. update them together or mark them explicitly BLOCKED/OPEN;
4. run the consistency preflight before proceeding.

## Objective progress evidence

Planning statement != progress.
Document created but not consumed != completed propagation.
Relevant commit = durable change.
Actions run = build attempt.
Verified artifact = APK produced.
CB6 real-device result = behavioral evidence.
Accepted real-device result = feature completion.

## Immediate rebuild order

1. Inventory and reconcile user requirements/change history.
2. Re-validate pinned CoMaps internal-analysis findings needed by each subsystem.
3. Inventory prior web/external research; refresh gaps from authoritative/current sources.
4. Reconcile real-device findings and known failures.
5. Rebuild the overall design from those inputs without treating the retired design as truth.
6. Compare rebuilt design with retired design to catch omissions, accepting an old item only after evidence validation.
7. Perform full consistency/impact review.
8. Mark the rebuilt design canonical only after the above is complete.
9. Resume Gate 1/other implementation only under the persistent gate mechanism.

