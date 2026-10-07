# CB6 Development Environment Redesign Concept — 2026-10-08

Status: RECORDED_CONCEPT_ONLY / NOT_ACTIVE / NOT_ADOPTED
Authority: User instruction to preserve the full discussed concept without omission.
Purpose: Preserve the complete redesign direction discussed after reviewing CB6 failures, GPT/agent capabilities and limitations, public successful agent-development patterns, and the current CB6 governance architecture.
Non-effect: This document does NOT modify the ACTIVE Development Method, Operational Rule Registry, Status Reporting, Feature Contracts, Signal/Convenience behavior, workflows, gates, Method Freeze, Auditor V2, APK, or application behavior. Adoption requires a separate explicit user approval after read-only inventory, feasibility review, impact review, and acceptance criteria are presented.

## 1. Problem statement

The redesign exists because CB6 repeatedly reached states where governance mechanisms were formally present or ACTIVE but did not guarantee that the actual current development work was audited or correct.

A central observed failure was the distinction between:
- proving that an auditor/verifier exists and is ACTIVE; and
- proving that the concrete current work unit actually passed that audit.

The redesign must never treat existence/registration/ACTIVE labels as execution evidence.

The user explicitly rejects a half-working governance feature that creates development overhead or false confidence.

## 2. Fundamental GPT/agent assumptions

The environment MUST be designed around actual GPT limitations rather than verbal promises.

Assumptions:
1. GPT is not deterministic and can forget, misinterpret, omit, or make incorrect judgments.
2. A prompt or conversational promise such as “always check X” is not a mechanical guarantee.
3. Chat memory is useful context but is not development authority or canonical state.
4. Switching roles inside one conversation from Developer to Reviewer is not proof of independent third-party review.
5. A separate reviewer agent can also be wrong; additional agents do not create absolute correctness.
6. Automatic invocation of a genuinely independent reviewer in the current CB6/ChatGPT/GitHub environment is UNPROVEN until demonstrated end-to-end.
7. Anything not demonstrated in the actual CB6 environment must be labelled UNPROVEN and must not be represented as guaranteed.
8. The design goal is therefore NOT “make GPT incapable of mistakes.”
9. The design goal IS “allow GPT mistakes, but prevent objectively unacceptable or incomplete work from passing the final exit.”

## 3. Core design principle

Canonical principle:

> Do not attempt to prove that AI is always correct. Build the development environment so that AI can be wrong without allowing unfinished, unapproved, stale, out-of-scope, or acceptance-failing work to pass the final exit.

The final safety boundary must depend primarily on deterministic facts, not semantic self-certification by the same GPT.

## 4. Target architecture

High-level target:

GitHub canonical repository/state
  -> Developer GPT
  -> research / cause analysis / proposal / evidence
  -> optional or required-when-proven independent Reviewer
  -> explicit user approval where required
  -> implementation
  -> tests / build / APK / real-device verification
  -> HARD EXIT GATE
  -> PASS only when all objective completion conditions pass

Reviewer AI is primarily a quality-improvement mechanism unless/until its independent execution and non-bypassability are proven in the real CB6 environment.

The Hard Exit Gate remains the final safety mechanism.

## 5. Four rule/enforcement classes

Every continuing rule should be classified by the type of enforcement it actually requires.

### A. Hard Constraint
Objective, deterministic conditions suitable for machine enforcement.

Examples:
- current HEAD/base freshness
- explicit approval evidence exists before an approval-bound implementation
- actual diff is within approved paths/scope
- forbidden scope is untouched
- required tests pass
- required build/APK evidence exists
- required real-device evidence exists
- acceptance criteria pass
- unresolved blocking failures are zero
- stale evidence cannot certify a newer HEAD

Enforcement: GitHub/CI/verifier/branch or workflow controls.

### B. Human Authority
Decisions that belong to the user and must not be inferred by GPT.

Examples:
- approve a concrete fix
- approve a specification change
- approve scope expansion
- accept a governance redesign

Enforcement: explicit user approval evidence; AI must not infer approval from context, silence, or a previous unrelated approval.

### C. Judgment Rule
Semantic development-quality decisions that cannot be reliably proven by a simple Python boolean.

Examples:
- whether multi-angle research is sufficient
- whether user intent has been understood
- whether the direct cause is actually established
- whether error-introduction cause and missed-detection cause are adequately explained
- whether alternative implementations were considered
- whether the proposed fix is unnecessarily broad
- whether the correct next state is RESEARCH, PROPOSE, CORRECT, STOP, etc.
- whether upstream CoMaps/source/web/device evidence has been compared appropriately

Enforcement: Developer reasoning plus independent reviewer when available/appropriate; never falsely labelled as deterministic proof.

### D. Regression / Eval
Concrete failures that have actually occurred and can be converted into repeatable detection.

Examples:
- a previously observed failure mode must not recur
- known fail-closed cases
- destructive tests for objective bypasses
- Signal topology-request failure must not silently produce an unacceptable completed state if that failure becomes an acceptance condition

Enforcement: regression test, eval, destructive test, or repeatable evidence check.

## 6. Preserve valuable existing CB6 principles

The redesign is NOT permission to discard existing safety work.

Preserve unless later inventory proves a safer replacement:
- GitHub as canonical state.
- Latest HEAD/base freshness and optimistic concurrency.
- Explicit user approval before approval-bound fixes (OPS-USER-APPROVAL-BEFORE-FIX-001).
- Acceptance Criteria fixed before implementation when applicable.
- Broad read-only investigation before a fix when cause is not already proven.
- Direct cause, error-introduction cause, missed-detection cause, impact, alternatives, recurrence prevention, and minimum-fix-scope analysis where applicable.
- No unrequested scope changes.
- Actual diff verification against approved scope.
- Fail-closed handling for objective safety gates.
- GitHub Actions raw logs/artifacts and real-device evidence as evidence sources.
- Real-device acceptance for behavior that CI cannot establish.
- Existing feature specifications unless explicitly changed.
- Existing Signal and Convenience behavior/specification boundaries.
- Status Reporting rules unless separately changed.
- Stop unnecessary diagnostics after fixed acceptance conditions are satisfied.
- Read-only parallel investigation while waiting when it cannot interfere with the running workflow.

## 7. Simplify governance structure without deleting meaning

Problem to avoid:
Rule -> candidate -> registry -> coverage -> verifier -> destructive test -> adoption evidence -> independent review -> freeze -> verifier-of-verifier proliferation for every semantic rule.

Desired direction:
- keep a small canonical development entry point;
- keep detailed feature specifications separate from development rules;
- keep current work state separately;
- keep unresolved known failures separately;
- keep repeatable regressions/evals separately;
- use deterministic gates only for conditions that can actually be determined mechanically.

Candidate simplified information architecture (names are conceptual, not yet adopted):
- DEVELOPMENT.md — short navigation/entry point for GPT and humans.
- RULES.md — canonical continuing development rules, classified A/B/C/D.
- specs/ — application/feature specifications.
- work/ — current work-unit state, base HEAD, approval state, acceptance state, next step.
- known-failures/ — unresolved verified failures/blockers.
- tests/ or evals/ — repeatable regression and destructive checks.

This structure is a design candidate only. Existing files must not be removed or merged until dependency and safety analysis is complete.

## 8. Keep application specification separate from governance rules

Feature behavior must not be mixed into general development governance.

Examples:
- Signal intersection normalization semantics
- 15 m direct/non-chain diagnostic rules
- 0.5 m MWM duplicate handling
- convenience zoom/icon behavior
- rendering behavior

These belong to feature specifications/contracts.

Governance determines whether development follows the specification; governance must not silently redefine the specification.

## 9. Small Work Unit concept

Retain the useful idea of a Work Unit, but reduce its purpose.

Primary purpose:
- reconstruct current work correctly across chats/time;
- record objective state, not prove every semantic decision.

Minimum useful content:
- work identity
- base/current HEAD binding
- goal
- current stage
- known verified failures
- current approval state and exact approval boundary
- acceptance state
- unresolved blockers
- evidence references
- next permitted action

Example conceptual state:
Work: Signal intersection normalization
Goal: one display per safely proven intersection
Known failure: topology request failure -> 962 acquired / clustered=0 / unacceptable many-signal display
Current stage: cause investigation
Approved change: none
Acceptance: failed/not accepted
Next: read-only comparison of ways to remove or avoid additional topology-network dependency

Work Unit state must never claim PASS merely because the auditor machinery exists.

## 10. Hard Exit Gate

The final completion boundary should be small and objective.

Candidate required conditions:
1. Work is bound to the current accepted HEAD/base.
2. Required user approval exists and matches the implemented change.
3. Actual diff is within approved scope.
4. Forbidden/unrequested scope is untouched.
5. Required automated tests pass.
6. Required build/APK evidence passes.
7. Required device evidence exists for device-dependent behavior.
8. All fixed Acceptance Criteria required for completion pass.
9. No unresolved blocking known failure remains.
10. Evidence is not stale relative to the code being accepted.

If any required condition is false or missing, completion is blocked.

The gate must not use “the GPT says this is complete” as evidence.

## 11. Real-device evidence is especially important for CB6

CB6 differs from ordinary server/web projects because behavior spans Android, CoMaps renderer, GPS, zoom, MWM, network, cache, JNI, device state, and floating-window operation.

CI cannot establish all user-visible behavior.

Therefore real-device acceptance must remain a first-class completion requirement for features whose acceptance depends on the physical device.

Concrete Signal lesson:
- fresh Overpass returned 962 points;
- additional topology retrieval failed;
- clustered=0;
- all 962 were retained/displayed;
- the safety policy avoided deleting uncertain signals but functional acceptance (“one intersection one icon”) failed.

A green code/build/governance gate must never override a required real-device acceptance failure.

## 12. Reviewer / third-party GPT policy

Desired role:
- challenge the Developer's assumptions;
- find missing research;
- compare alternative hypotheses;
- detect user-intent mismatch;
- challenge root-cause certainty;
- detect unnecessarily broad fixes;
- evaluate whether the next development stage is appropriate;
- review important post-implementation evidence.

Non-guarantees:
- a reviewer GPT is not infallible;
- same-chat role switching is not mechanically independent;
- a separate prompt alone does not prove independent execution;
- automatic reviewer invocation in CB6 is not assumed.

Until proven:
- Reviewer is a quality-improvement layer, not the sole safety boundary.
- The Hard Exit Gate must remain safe even if reviewer automation is unavailable.

If future PoC proves independent reviewer automation, the following must be demonstrated before it becomes mandatory:
1. reviewer runs as a genuinely separate execution/context;
2. developer cannot fabricate/overwrite reviewer approval;
3. reviewer omission is detected;
4. bypassing reviewer blocks the required transition;
5. reviewer failure/time-out fails safely;
6. credentials/permissions are separated appropriately;
7. operation is practical from the user's smartphone-centered workflow;
8. cost/API/entitlement requirements are explicit;
9. destructive tests prove non-bypassability.

## 13. No verbal-only guarantees

A continuing requirement that cannot be mechanically guaranteed must not be described as mechanically enforced.

Required terminology:
- PROVEN: demonstrated in the actual CB6 environment, including bypass/destructive test where relevant.
- MACHINE_ENFORCED: only for a condition actually enforced on the relevant real path.
- UNPROVEN: plausible/design-level but not demonstrated.
- AI_JUDGMENT: semantic judgment performed by GPT/Reviewer, not deterministic proof.
- USER_AUTHORITY: requires explicit user decision.
- RECORDED_CONCEPT_ONLY: documented but not adopted.

Prohibited inference:
- “ACTIVE auditor exists” => “this work was audited.”
- “verifier file exists” => “verifier ran on this work.”
- “review prompt exists” => “independent review occurred.”
- “GPT promised to remember” => “future compliance is guaranteed.”
- “CI is green” => “device behavior is accepted.”

## 14. Adoption order must be proof-first, not architecture-first

Previous risky order:
concept -> documents -> verifier -> ACTIVE -> discover later that the real path bypasses it.

Preferred order:
1. read-only inventory of current governance and dependencies;
2. classify each rule/control into Hard Constraint / Human Authority / Judgment / Regression-Eval;
3. identify duplicate and conflicting mechanisms;
4. identify every safety property currently provided;
5. design the minimum replacement;
6. test replacement on an isolated candidate path;
7. intentionally bypass/violate it;
8. prove it stops the violation;
9. prove existing feature behavior is unchanged;
10. only then request explicit adoption approval;
11. migrate incrementally;
12. remove old mechanisms only after replacement equivalence is proven.

No “big bang” governance deletion.

## 15. What should be tested in a future PoC

Before claiming a new environment works, intentionally test:
- missing approval;
- stale HEAD;
- out-of-scope diff;
- missing required evidence;
- failing required test;
- failing device acceptance;
- unresolved blocker;
- stale evidence from older commit;
- skipped reviewer if reviewer becomes mandatory;
- forged/self-created review evidence if independence is claimed;
- reviewer unavailable/time-out;
- new chat reconstruction from repository only.

Expected result: unsafe/incomplete work cannot reach the completion state.

## 16. Relationship to successful external agent-development patterns

The redesign intentionally follows principles seen in successful/public agentic development environments, without copying their scale:
- repository/system-of-record rather than relying on chat memory;
- short navigation/entry documents rather than giant instruction files;
- structured repository knowledge;
- human authority for consequential approval;
- deterministic CI for objective conditions;
- agents for semantic development work;
- traces/evidence and regression/evals for observed failures;
- minimal agent count; add separate agents only where separate context/ownership materially helps;
- do not trust an agent merely because it produced a confident answer.

CB6-specific adaptation:
- keep the system small enough for one user + ChatGPT + GitHub + GitHub Actions + Android device;
- do not recreate enterprise-scale multi-agent infrastructure unless proven necessary;
- make real-device evidence stronger than typical web-project CI because CB6 behavior depends on device/render/network/GPS state.

## 17. Scope of future inventory

Before adoption, inspect all current governance mechanisms and map them to the proposed model, including at minimum:
- Development Method contract and documentation;
- Operational Rule Registry;
- Rule Coverage;
- Method Freeze;
- Root Certification;
- verification mechanisms;
- workflow meta verification;
- approval-before-fix rule;
- Development Efficiency rule;
- Status Reporting;
- monitoring rules;
- Auditor V1/V2 and work-unit machinery;
- independent review;
- feature gates;
- impact/research records;
- APK evidence;
- device evidence;
- final acceptance;
- destructive/fail-closed tests;
- Signal/Convenience feature contracts and specifications.

For every item classify:
- KEEP;
- MERGE/SIMPLIFY;
- MOVE_TO_AI_JUDGMENT;
- MOVE_TO_FEATURE_SPEC;
- MOVE_TO_REGRESSION/EVAL;
- REMOVAL_CANDIDATE;
- UNKNOWN/NEEDS_PROOF.

For every removal candidate identify:
- what safety property it currently provides;
- what replaces that property;
- how replacement equivalence will be proven;
- what bypass test will be used.

## 18. Explicit non-goals

This concept does NOT:
- authorize deleting existing governance;
- authorize changing ACTIVE rules;
- authorize changing Method Freeze;
- authorize modifying Signal or Convenience;
- authorize a new fix;
- authorize automatic commits beyond recording this concept;
- claim independent GPT review is already available;
- claim GPT can be made error-free;
- claim every semantic rule can be machine verified;
- claim the proposed file layout is final.

## 19. Current recommendation

Do not patch Auditor V2 incrementally merely to preserve the current architecture.

Next recommended step is a read-only, complete inventory and dependency map of the existing CB6 governance against this concept.

Only after that inventory should a concrete migration candidate, risks, Acceptance Criteria, and exact changed files be presented for explicit user approval.

## 20. User intent preserved by this record

The redesign must solve the user's recurring concerns:
- rules and development methods must not be forgotten;
- the assistant must not proceed before sufficient confirmation/research;
- multi-angle investigation must occur when needed;
- user intent must not be silently changed;
- unapproved changes must not be made;
- evidence must reflect the real current build/device state;
- a governance mechanism must not be called functional merely because its files exist;
- half-working governance that slows development is unacceptable;
- impossible or unproven capabilities must not be promised verbally as if they are guaranteed;
- GPT capabilities, limitations, memory/context behavior, tool structure, and agent independence must be considered explicitly;
- the environment should align with successful agent-development principles while remaining practical for CB6;
- the final environment should reduce wasted diagnostics, repeated discussion, and governance maintenance while increasing actual safety;
- important prior rules must not be lost during simplification;
- the user must retain authority over adoption and approval-bound changes.

---
Recorded from the 2026-10-08 CB6 governance redesign discussion.
This record is intentionally non-ACTIVE until separately reviewed and explicitly adopted.
