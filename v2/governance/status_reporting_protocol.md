# CB6 Status Reporting Protocol

Status: PROPOSED  
Rule ID: `OPS-STATUS-REPORTING-001`  
Source: explicit user continuing instruction, 2026-09-30; four-line reporting extension explicitly requested 2026-10-02

## Required progress classification

Every CB6 progress report MUST explicitly state one of these classifications:

- **進めて推奨** — work can continue on the assistant/GitHub side, including work already in progress or work that can be accelerated without user-only action.
- **待ち** — blocked on an external result such as GitHub Actions. The report MUST identify the Run/result being awaited and give an approximate next-check time.
- **スマホ操作が必要** — the next required evidence/action can only be performed by the user on the physical device, such as installation or real-device verification.

## Required four-line progress template

Every CB6 progress report MUST include all four lines below, with values that reflect the current verified state:

1. **分類** — exactly one of `進めて推奨`, `待ち`, or `スマホ操作が必要`.
2. **次にユーザーがすること** — state the exact next user action. When no device/user-only action is required and assistant-side work can continue, use `「進めて」`.
3. **ChatGPTアプリ** — explicitly state whether the ChatGPT app may be closed. When no foreground user interaction is required, use `閉じてOK`.
4. **スマホ操作** — explicitly state whether smartphone/CB6 operation is required. When it is not required, state `不要`; when retry is also unnecessary, state `再試行もしなくて大丈夫です`.

Canonical no-user-operation form:

- **分類：進めて推奨**
- **次にユーザーがすること：「進めて」**
- **ChatGPTアプリ：閉じてOK**
- **スマホ操作：不要。再試行もしなくて大丈夫です。**

For `待ち`, the same four-line structure MUST be retained and the classification line or immediately adjacent status text MUST identify the awaited Run/result, approximate wait time, and next-check timing as required below. For `スマホ操作が必要`, the second and fourth lines MUST state the concrete operation/evidence required rather than using the no-operation wording.

## Parallel work while waiting

While an external result is pending, non-conflicting read-only investigation, repository inspection, static analysis, and evidence review MAY continue. Waiting for one result is not a reason to stop unrelated safe work.

## Progress-query freshness

When the user asks `進捗は？` or an equivalent progress-status question, the report MUST NOT rely on chat memory or a prior notification. Before reporting, re-fetch the current GitHub branch HEAD, relevant Actions Run state, and relevant raw job logs where log evidence is material.

## Fix-commit approval boundary

Before beginning an implementation-problem fix commit, follow `OPS-USER-APPROVAL-BEFORE-FIX-001` or its adopted successor. Present the concrete proposed change and obtain change-bound individual user approval before implementation begins.

## Deferred candidate — new-chat rule-ingestion cross-check

Out of scope for this change. Record only as a future candidate: if later required, consider a mechanism that checks at new-chat/session start whether confirmed continuing rules have been durably incorporated into GitHub authority. Do not design, implement, verify, or adopt that mechanism as part of `OPS-STATUS-REPORTING-001`.

## Adoption and verification

This protocol enters the existing lifecycle as `PROPOSED`. It MUST NOT be treated as ACTIVE or enter MACHINE_ENFORCED coverage until required lifecycle evidence exists.

Use the existing adoption lifecycle without creating a new mechanism: **Verifier → destructive test → independent review → explicit adoption**.

The intended machine-verification source is the latest progress-report message. The existing lifecycle's verifier candidate MUST verify all four required template fields and their state-consistent values, including exactly one of the three required classifications. For `待ち`, it MUST also verify that the awaited external result, approximate wait time, and next-check time are present. Destructive tests MUST demonstrate rejection when any required template field is absent or inconsistent. Until the existing lifecycle completes verifier proof, destructive proof, independent review, and explicit adoption, this rule remains non-ACTIVE.
