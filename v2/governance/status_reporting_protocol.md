# CB6 Status Reporting Protocol

Status: ACTIVE (Status Reporting v10)  
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

For `待ち`, the same four-line structure MUST be retained. In addition to the awaited Run/result, every `待ち` report MUST explicitly state all existing ACTIVE v10 required wait fields: **目安時間** (`approximate_wait_time`), **次回確認タイミング** (`next_check_timing`), **待機中にできる対応の有無** (`parallel_work_available`), and **待機後の指示** (`post_wait_user_instruction`). For `スマホ操作が必要`, the second and fourth lines MUST state the concrete operation/evidence required rather than using the no-operation wording.

## Wait-time display

For a newly awaited GitHub Actions Run, the first `待ち` progress report for that Run MUST show the Run start time in JST.

For the second and every later `待ち` progress report for the same Run, the report MUST show the cumulative elapsed time measured from that same Run start time instead of resetting the wait basis to the latest check.

Intermediate progress checks MUST NOT reset the Run start-time basis. When the awaited Run changes to a different Run, the first `待ち` report for the new Run starts again by showing that new Run's start time in JST.

### First wait guidance for a new Run

For the first `待ち` report of a newly awaited Run, the recommended next-check interval MUST use the actual execution duration of the most recent completed Run of the same workflow when that observation is available and reasonably representative. Do not substitute a fixed default interval such as 15 minutes merely because this is the first check. For example, if the immediately preceding comparable Run completed in approximately 19 minutes, the initial next-check guidance for the new Run should be approximately 19 minutes.

If no same or reasonably comparable actual-duration evidence is available, the official next-check guidance MUST be `所要時間不明`; unsupported fixed estimates are forbidden. Only when official guidance is `所要時間不明` and concrete GitHub execution evidence supports a reference estimate, display `所要時間不明（参考推測：約○〜○分）`. The estimate basis is normally hidden and is shown when the user asks for the basis.

### Historical duration reference for future wait estimates

Future wait-time guidance MUST use the actual execution duration of recent completed Runs of the same workflow as a reference when that history is available. Actual execution duration is measured from the GitHub Actions Run start timestamp to its completion timestamp; it is NOT measured from the user's progress-check interval.

The user's next progress check may occur minutes, hours, or days later. That delay MUST NOT be added to, substituted for, or otherwise distort the recorded Run duration.

For an in-progress Run, reports MUST distinguish the current elapsed time from the recommended next-check interval. The recommended next-check interval SHOULD be based on recent actual durations for the same workflow, so repeated unnecessary checks can be reduced. Completed Run durations SHOULD be retained as reference observations for later Runs of that workflow.

If the user checks after the Run has already completed, report the completed result rather than presenting the user's elapsed absence as wait time.

For every intermediate check while the same Run remains in progress, the recommended next-check interval MUST be recalculated from the Run's original start time and the recent actual duration history for that workflow. It MUST represent the remaining recommended interval from the current check; an earlier interval (for example, 15 minutes) MUST NOT be reset or repeated merely because another progress check occurred. If the Run has already exceeded the normal recent duration range, use a shorter reasonable next-check interval rather than restarting the original interval.

The historical Run durations and the calculation/reasoning used to derive the recommended next-check interval MUST NOT normally be displayed in progress reports. They remain internal/reference evidence and MUST be shown only when the user asks for the reason, basis, past wait times, or equivalent detail. The resulting next-check guidance itself remains visible as required by this protocol.

Routine progress reports MUST also omit explanatory prose stating that an intermediate check does not reset the wait timer, that the next-check interval has been recalculated, or equivalent descriptions of the wait-calculation mechanism. Apply that mechanism silently and display only the required wait status values (such as cumulative elapsed time and the resulting next-check guidance). Explain the mechanism only when the user explicitly asks about it.

## Parallel work while waiting

While an external result is pending, non-conflicting read-only investigation, repository inspection, static analysis, and evidence review MAY continue. Waiting for one result is not a reason to stop unrelated safe work.

## Progress-query freshness

When the user asks `進捗は？` or an equivalent progress-status question, the report MUST NOT rely on chat memory or a prior notification. Before reporting, re-fetch the current GitHub branch HEAD, relevant Actions Run state, and relevant raw job logs where log evidence is material.

### Known tracked Actions Run ID

When the relevant GitHub Actions Run ID is already known, progress/status checks MUST directly re-fetch that Run ID as the primary state source. Actions run listings are supplementary discovery/context only. A tracked Run being absent from a listing MUST NOT by itself be interpreted as deleted, completed, failed, or otherwise state-changed.

## Fix-commit approval boundary

Before beginning an implementation-problem fix commit, follow `OPS-USER-APPROVAL-BEFORE-FIX-001` or its adopted successor. Present the concrete proposed change and obtain change-bound individual user approval before implementation begins.

## Deferred candidate — new-chat rule-ingestion cross-check

Out of scope for this change. Record only as a future candidate: if later required, consider a mechanism that checks at new-chat/session start whether confirmed continuing rules have been durably incorporated into GitHub authority. Do not design, implement, verify, or adopt that mechanism as part of `OPS-STATUS-REPORTING-001`.

## Response Preflight

Before every CB6 progress/status response, ChatGPT MUST use current GitHub authority, select applicable ACTIVE rules, check the intended response against those rules, and correct or withhold a response when the preflight does not pass. Chat memory alone is not authority.

GitHub machine verification covers repository contract, verifier/destructive-test behavior, Registry/Coverage linkage, and fail-closed specification. It does not claim to intercept or mechanically block ChatGPT response transmission. Runtime preflight execution is a ChatGPT operational responsibility.

## Adoption and verification

Status Reporting v10 is `ACTIVE`, bound by `v2/gates/status_reporting_contract_v10.json`, registered by `v2/gates/operational_rule_registry_v16.json`, with `MACHINE_ENFORCED` repository-contract coverage in `v2/gates/rule_coverage.json`.

The adoption lifecycle remains: **candidate verification → destructive test → independent review → explicit adoption → MACHINE_ENFORCED coverage**.
