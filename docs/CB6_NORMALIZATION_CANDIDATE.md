# CB6 Governance Normalization — candidate phase 5

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

## Fixed end state — normalization completion criteria (phase 4)

This section records the destination, not a declaration of completion. It does not replace the ACTIVE Development Method, Rule Registry, Feature Contracts, frozen-feature authorities or acceptance evidence. In a conflict, resolve against the latest ACTIVE GitHub authority and seek explicit user approval before changing this destination.

Completion requires **all applicable** criteria, with links to verifiable evidence rather than assertions:
1. **Method compliance:** current HEAD, active requirements, source/research/impact, prior scoped user approval, direct and destructive tests, and independent review are followed where required by ACTIVE authority.
2. **Feature protection:** no unauthorized change or removal of existing Signal, Convenience, CoMaps or other protected app behavior; changes are assessed against relevant feature contracts and regression evidence.
3. **Evidence-based outcomes:** a successful workflow is method/test evidence only. Build provenance, APK identity/signature/hash and actual CB6 device acceptance are separate requirements when application behavior or a releasable APK is in scope. A documentation-only candidate does not manufacture or imply new APK/device evidence.
4. **Proportionate governance:** identify overlapping controls and excessive proof chains; simplify only after demonstrating equivalent safety and receiving separate adoption approval. No legacy gate retirement merely because the candidate CI passes.
5. **Continuity:** another chat/session can recover the fixed destination, current authority, verified evidence, outstanding blockers and next safe action from GitHub without relying on conversation memory.

**Completion decision:** COMPLETE is prohibited while any applicable criterion lacks valid evidence or any blocking review/approval/regression issue remains. Mark N/A only with explicit scope reasoning and supporting authority; never use N/A to bypass application acceptance for an app release.

## Current position (evidence snapshot; refresh before every decision)

- Source of truth: base `cb6-v2-clean`; candidate PR #4 `poc/governance-normalization-candidate-phase1`. This snapshot was prepared from base HEAD `645132832a478025e162d0f9fea2e785bcba374e` and candidate HEAD `0a8f51c74d756b4ed57ee72e2d5ef9f7ac115509`; **historical after the next commit**.
- Candidate: Draft, unmerged, four candidate files in the PR. Phase 3 candidate workflow succeeded on that candidate HEAD (Run 37731296043). This is not formal adoption or release acceptance.
- At the last inspected state, Development Gate Run 37731296068 was still in progress; its outcome must be freshly queried. Independent GitHub reviews: zero; base branch protection: false.
- Not complete: independently verifiable approval linkage, independent review and unresolved-thread evidence, current-head Development Gate result, any applicable APK/device acceptance, equivalence of simplified governance, future-feature coverage and formal adoption.
- Candidate status: **IN PROGRESS / RELEASE_BLOCKED**, not COMPLETE. This table is a checkpoint, not an evergreen live status claim.

## Open issues and next evidence

| Item | Required evidence / next action |
| --- | --- |
| Current CI | Query latest candidate and Development Gate runs for the current PR HEAD; never reuse a prior-SHA result |
| Independent review | Obtain independent review on current SHA and check the latest effective states and unresolved threads |
| Approval provenance | Bind exact prior user authorization to the proposed change without treating chat text as GitHub-authenticated proof |
| Governance equivalence | Compare old/new coverage, negative tests and omitted obligations before proposing ACTIVE adoption |
| APK and CB6 device | Require build identity and real-device acceptance if application change/release is proposed; keep separately blocked otherwise |
| Branch safeguards | Verify actual protection/required checks or document a separately approved equivalent safeguard |

## Resume protocol (including after long delays or a new chat)

1. Fetch latest GitHub base and PR HEAD, PR diff, reviews and current-SHA workflow results. Stop and resynchronize if HEAD has changed.
2. Read current ACTIVE Development Method, Rule Registry, Feature Contracts, specifications and relevant protection rules. Do not elevate historical or candidate text over ACTIVE authority.
3. Read the fixed end-state criteria above and compare each against current verifiable evidence; mark VERIFIED, PENDING, BLOCKED or NOT_APPLICABLE_WITH_REASON.
4. Identify the earliest unsatisfied prerequisite and the smallest safe next step; research and assess impact before implementation.
5. Require fresh, change-specific prior user approval before any further modifications. Preserve PR Draft and existing gates until independently justified adoption.
6. Record the new HEAD, evidence, blockers and next step here after an explicitly approved documentation change. Never claim completion based solely on a previous chat or a green CI.

## Destination change control

Progress/evidence updates must **not** silently weaken, delete, relabel or redefine these completion criteria. A substantive change to the destination or acceptance threshold requires a stated reason, impact/authority consistency check and **prior explicit user approval tied to that exact change**. Keep the previous criteria visible in version history. The phase 4 approval authorizes this documentation addition only, not later edits or ACTIVE adoption.

## Phase 5 — bounded evidence classification (candidate only)

- Review-thread status is fetched from GitHub GraphQL at the current PR, including the resolved flag. API errors, malformed responses and truncated pagination are audit errors; unresolved threads remain release blockers. An empty verified list is not treated as an unverified list.
- The existing historical governance/efficiency independent-review workflows do **not** review this candidate SHA merely by existing. A separately named `CB6 Governance Normalization Independent Review` workflow success on the same HEAD is checked as independent automation evidence. Until a genuine separate workflow run exists, the release blocker remains. Automated review is never mislabeled as a human GitHub approval.
- GitHub independent human review remains separately required under the current candidate criteria; with no separate reviewer available, it remains blocked pending explicit, authority-consistent decision. No self-review or invented reviewer.
- APK provenance and CB6 real-device acceptance are **not applicable to this four-file documentation/audit-only candidate**, because it changes no app runtime and produces no releasable APK. The condition becomes mandatory again for any app behavior change or APK release; no device acceptance is inferred.
- Prior approval authenticity remains a release blocker, not a successful proof. The existing approval contract's `CANDIDATE` status cannot itself establish ACTIVE authenticated evidence.
- Base branch protection remains a blocker until actual protection or a separately approved and verified equivalent exists.
- Candidate audit success is a read-only evidence-consistency result, not independent review, release authorization, formal adoption, or permission to retire old gates.
- The phase 5 change is restricted to the existing candidate verifier, destructive tests and this document. The existing candidate workflow, ACTIVE authorities and application behavior remain unchanged.

**Phase 5 acceptance:** current-SHA CI and destructive tests must pass; malformed or missing evidence must not silently become a PASS; any unproven independent/approval/branch safeguard must remain RELEASE_BLOCKED. The fixed end-state criteria above are unchanged.

## Phase 6 — separate-run reconstruction candidate

The existing candidate workflow now supports an explicit `workflow_dispatch` with `review_mode=independent-review`. Its separate job checks out the exact run SHA with full history, reconstructs the four-file PR diff against `cb6-v2-clean`, verifies the two relevant ACTIVE rule identities, and reruns destructive tests. The pull-request candidate job is unchanged in purpose. The dispatch job is a **candidate evidence reconstruction**, not a certified independent human reviewer or proof of independent context; no dispatch run is claimed until GitHub Actions actually records one. The verifier continues to block missing `CB6 Governance Normalization Independent Review` same-SHA evidence and missing human GitHub approval; this dispatch does not spoof that workflow name. Existing blockers for approval authenticity and branch protection remain. Do not treat dispatch success as formal independent acceptance, release or merge authorization.

## Phase 6 execution-path correction (approved)

The phase-6 `workflow_dispatch` entry was not operable because GitHub requires a dispatchable workflow file on the default branch. The existing candidate workflow is PR-only, and the reconstruction job is now triggered by the same `pull_request` event as the candidate job. It checks the actual PR merge checkout SHA, base-relative four-file scope, ACTIVE registry entries and destructive tests. This removes the unnecessary phone/manual workflow trigger. It **does not** constitute a separate independent workflow, certified independent review context, or GitHub human approval; the existing independent-review, approval-authenticity and branch-protection release blockers remain. The new regression test prevents silently restoring the unavailable dispatch trigger or claiming false independent acceptance. No ACTIVE gate or application behavior is changed.
