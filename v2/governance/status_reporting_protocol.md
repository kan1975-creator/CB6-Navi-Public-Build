# CB6 Status Reporting Protocol

Status: PROPOSED  
Rule ID: `OPS-STATUS-REPORTING-001`  
Source: explicit user continuing instruction, 2026-09-30

## Required progress classification

Every CB6 progress report MUST explicitly state one of these classifications:

- **進めて推奨** — work can continue on the assistant/GitHub side, including work already in progress or work that can be accelerated without user-only action.
- **待ち** — blocked on an external result such as GitHub Actions. The report MUST identify the Run/result being awaited and give an approximate next-check time.
- **スマホ操作が必要** — the next required evidence/action can only be performed by the user on the physical device, such as installation or real-device verification.

## Parallel work while waiting

While an external result is pending, non-conflicting read-only investigation, repository inspection, static analysis, and evidence review MAY continue. Waiting for one result is not a reason to stop unrelated safe work.

## Progress-query freshness

When the user asks `進捗は？` or an equivalent progress-status question, the report MUST NOT rely on chat memory or a prior notification. Before reporting, re-fetch the current GitHub branch HEAD, relevant Actions Run state, and relevant raw job logs where log evidence is material.

## Fix-commit approval boundary

Before beginning an implementation-problem fix commit, follow `OPS-USER-APPROVAL-BEFORE-FIX-001` or its adopted successor. Present the concrete proposed change and obtain change-bound individual user approval before implementation begins.

## Adoption and verification

This protocol enters the existing lifecycle as `PROPOSED`. It MUST NOT be treated as ACTIVE or enter MACHINE_ENFORCED coverage until required lifecycle evidence exists.

The intended machine-verification source is the latest progress-report message: a verifier should confirm that one of the three required classifications is explicitly present and, for `待ち`, that the awaited external result and approximate next-check time are present. Until that mechanism is designed, reviewed, and proven with destructive tests, this rule remains non-ACTIVE.
