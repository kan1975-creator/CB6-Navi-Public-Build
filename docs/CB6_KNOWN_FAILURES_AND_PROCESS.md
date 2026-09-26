# CB6 Known Failures and Mandatory Development Process

This file exists so the development method does not regress after a time gap or new session.

## Mandatory process — applies to every current and future CB6 task

1. Do not fix only the failing line.
2. Identify the changed concept/name/flow.
3. Search the entire repository for old references and old assumptions.
4. Inspect implementation scripts, generated-source templates, audits, workflow grep/invariants, resources and regression checks.
5. Inspect workflow ordering for later scripts that can restore stale behavior.
6. Update all affected implementation and validation locations together.
7. Check frozen/completed features for unintended changes.
8. Check known historical failure patterns and Python/Java/C++ syntax before build.
9. Inspect final generated source, not only patch source.
10. Build only after the full preflight.
11. On failure, repeat the root-cause sweep.
12. Never change correct implementation merely to satisfy a stale validator; update the validator when it no longer represents the specification.
13. GitHub Actions success is not completion. APK verification + CB6 real-device behavior is final authority.
14. Minimize build count through analysis/preflight.

## Known failure classes

### Stale renamed-flow validators
Historical example: `buildPoiQuery` was replaced by split convenience/stop acquisition, but old scripts/audits still required the obsolete name. Multiple builds were wasted by finding these one at a time.

Prevention: repository-wide obsolete-symbol search before build; audits should verify required behavior, not arbitrary implementation names.

### Literal escaped newline contamination
Python patch generation has produced literal `\\n` in Java/C++/validator output.

Prevention: parse Python scripts before build; inspect generated Java/C++ anchors; do not assume a Python string rendered as intended.

### Later patch restores old state
Sequential `apply_cb6_*` scripts and configure/resource generation can overwrite earlier changes.

Prevention: treat workflow order as architecture; inspect final generated tree after all final patches.

### UserMark group mismatch
A class derived from `DebugMarkPoint` may default to `DEBUG_MARK`. If JNI clears/shows `CB6_DRIVING`, the mark can be created into a different group and never appear as intended.

Prevention: audit constructor mark type + ClearGroup + SetIsVisible + CreateUserMark + NotifyChanges together.

### Whole-group replacement erases unrelated marks
`nativeSetCb6DrivingMarks` rebuilds the CB6 mark group. A signal-only update can erase stores/stops.

Prevention: merge retained non-signal marks before publish; dedicated schedulers must share a coherent retained dataset.

### Build success mistaken for feature success
Run #87/#91 examples: valid arm64 APK does not mean convenience icons are visible.

Prevention: acceptance state remains NOT FROZEN until user verifies on CB6.

### Network dependency where MWM already contains data
Stock CoMaps can already show many POIs from downloaded MWM. Duplicating them via Overpass adds failure modes.

Prevention: before network supplementation, inspect native MWM/classificator/style path and prefer it when it can satisfy the spec.

## Debugging hierarchy

For a missing map feature, check in this order:
1. Is feature present in MWM/search/place data?
2. Is correct internal classificator type/brand available?
3. Does active default/vehicle style include it at this zoom?
4. Does symbol exist in generated atlas?
5. Is overlay blocked by priority/collision? Use `?debug-rect` where useful.
6. For UserMarks: did data reach Java parser?
7. Did retained dataset contain it?
8. Did JNI receive it?
9. Correct UserMark type/group?
10. Correct symbol name and zoom?
11. Did a later update clear the group?

This ordering prevents repeatedly rebuilding the renderer when acquisition is actually zero, and vice versa.

## Documentation maintenance rule

When architecture knowledge changes, update:
- `CB6_COMAPS_ARCHITECTURE.md`
- `CB6_CHANGE_IMPACT_MAP.md`
- `CB6_FROZEN_FEATURES.md`
- this file
in the same change where practical.


## CB6 second-generation restart policy — MANDATORY

The user explicitly approved a development restart whose purpose is to reset technical debt, **not** to reset the product specification or discard proven work. This policy is persistent and must be consulted before future CB6 implementation work.

1. Preserve the current `clean-import` history and successful APK/runs as reference; never destroy the comparison baseline.
2. Start second-generation implementation from the pinned clean CoMaps baseline, not by blindly copying the accumulated patch stack.
3. Carry forward all formal CB6 specifications, architecture/internal-analysis records, known-failure records and regression knowledge.
4. Carry forward real-device accepted/frozen behavior as evidence and preserve every non-superseded clause. Run #65 signal behavior is historical evidence; where a later active Requirement Registry entry explicitly changes it (for example `SIG-200M-001`), the active requirement and current spec take precedence. Port only proven implementation that remains compatible and regression-test it.
5. Do not carry forward obsolete experiments, stale validators, redundant patch layers, temporary probes or accidental implementation constraints merely because they exist in the old branch.
6. Prefer CoMaps' native architecture/data path first: native MWM/core capability > minimal native extension > isolated CB6 custom implementation > external network supplementation.
7. Organize CB6 additions by responsibility (map data/POI, rendering, location/camera, navigation/routing, search/voice, UI/settings) instead of a long chronological stack of patches.
8. Consolidate stable modifications so later scripts cannot silently undo earlier behavior. Patch ordering must remain explicit and audited.
9. Audits verify specifications and regressions, not arbitrary historical function names.
10. Before implementing each feature, consult `CB6_COMAPS_ARCHITECTURE.md`, `CB6_PINNED_COMAPS_INTERNAL_ANALYSIS.md`, `CB6_CHANGE_IMPACT_MAP.md`, and `CB6_FROZEN_FEATURES.md`.
11. For data already present in MWM (convenience, fuel, facilities), prove actual existing-map type/name/brand/operator availability before choosing a network duplicate path.
12. Development gate remains: architecture/impact analysis -> repo-wide search -> implementation -> obsolete-flow check -> syntax/generated-tree preflight -> build -> APK verification -> CB6 real-device test -> freeze.
13. GitHub Actions success alone never marks a feature complete.
14. The restart must improve maintainability without changing user-requested behavior outside the feature being worked on.

This section is an absolute project rule. Do not revert to incremental one-error-at-a-time patch accumulation after a time gap or new chat.


## Persistent development continuity and progress-proof rule — MANDATORY

The user expected the project to already operate as a GitHub-persistent development loop. Repeated cases where an automation run occurred but no implementation commit, build run, or artifact advanced the project are a process failure. Future CB6 work must not treat automation execution itself as development progress.

1. GitHub is the persistent source of truth for development state. Chat titles, automation summaries, and conversational claims are not authoritative.
2. Every development stage must leave a durable GitHub checkpoint that a later run/chat can resume without reconstructing intent from conversation history.
3. The current stage and next executable action must be derivable from repository state, workflow state, and formal docs. Do not depend on the user repeating "continue".
4. Automation is a supervisor/resumer, not proof of work. A successful automation invocation with no repository/workflow advancement is **NO DEVELOPMENT PROGRESS**.
5. Progress may be claimed only from objective evidence:
   - implementation progress: a relevant Git commit exists;
   - build progress: a new relevant GitHub Actions run exists;
   - APK progress: a verified artifact exists;
   - feature completion: required CB6 real-device acceptance exists.
6. If an automated cycle cannot advance the current implementation stage, it must identify the blocking/root cause from actual GitHub state. It must not silently substitute more planning/documentation for the required implementation unless that documentation is an explicit gate prerequisite.
7. When the next gate is implementation, prioritize source implementation and build initiation over additional non-blocking design work.
8. Build/fix loops must persist through GitHub: commit the coherent fix, run the workflow, inspect logs, perform the repo-wide root-cause sweep required by this document, and continue from the resulting state on the next execution.
9. Do not report "device-test waiting" until the exact feature APK has been built, artifact-verified, and is genuinely ready for the user to install.
10. Separate/new automation chats must never create an alternative project state. The canonical project state is GitHub plus these formal project documents.
11. Time gaps, model/chat changes, or automation restarts must not reset these rules or the second-generation policy above.
12. For status reports use the strict interpretation: **no relevant commit = implementation not advanced; no relevant Actions run = build not started; no artifact = APK not produced; no real-device confirmation = feature not complete.**
13. The intended operating loop is: read durable GitHub state -> determine current gate -> execute the next concrete action -> persist result in GitHub -> build/verify when applicable -> record blocker or advance gate. Merely re-reading state is not a completed development cycle.
14. Active CB6 requirements, non-superseded accepted behavior, Hokkaido-only scope, current architecture authority, proven-implementation evidence, and regression rules remain mandatory across every resumed cycle. Historical/frozen records cannot override an explicit later active requirement.

This continuity rule is part of the permanent CB6 development policy and must be consulted together with the second-generation restart policy before implementation or automation changes.

## Gate 1 preflight finding — 2026-09-26

Full repository Python compilation found a literal `\\n` between the `mgr` and `fw` assignments in dormant `CB6_CONVENIENCE_AUDIT.py`. Converted only that separator to a real newline. This audit is not executed in V2 and its historical feature requirements are not imported. Gate 1 compiles all Python references to detect syntax contamination before any expensive build.

The V2 signal gate additionally validates enum/constructor/publisher group identity, exact atlas names in every density/theme, template byte identity after configure, and the packaged JNI/arm64 ELF. A source SVG alone and a successful Gradle task are still insufficient evidence.


## Repeated stale-audit regression — root cause and structural fix — 2026-09-26 — MANDATORY

This is a recurrence of a failure the user had already identified: an implementation/specification change is made, but an audit, APK verifier, test, workflow grep, generated-resource check, or historical invariant still encodes the previous implementation. The existing rule to "search the entire repository" was necessary but not sufficient because it was a **process instruction only**; nothing mechanically prevented a commit/build when that instruction was incompletely executed.

### Why the previous rule did not eliminate the problem

1. **Specification values were duplicated.** The same behavior was encoded independently in implementation code, audit literals, tests, workflow checks, resource lists, and documentation. A correct implementation edit could therefore leave a stale validator behind.
2. **The preflight checked many files but did not test validator/spec consistency itself.** Gate 1 could prove source/generated-tree consistency and still allow an APK-only assertion to retain a historical symbol requirement.
3. **Source audit and packaged-APK audit had different assumptions.** In the 2026-09-26 recurrence, z15/200m changed from `cb6-signal-s` to the same thin `cb6-signal-xs` used at z14/500m. The source audit was updated, but the APK audit still iterated a hard-coded `xs/s/m/l` list and required `cb6-signal-s` in `liborganicmaps.so`. Gradle therefore built a valid APK and only the final verifier failed.
4. **Historical "frozen" assertions were treated as implementation details rather than behavioral requirements.** A frozen feature must preserve user-accepted behavior unless the user explicitly changes it. Once the user explicitly changes 200m size, the old symbol name is no longer a frozen requirement.
5. **Repository-wide search was not a hard gate tied to the changed concept.** The rule existed in documentation, but a developer/automation run could still miss a second representation of the concept and proceed to an expensive build.

### Structural correction

For every feature change, the change unit is now:
`formal/current spec -> single feature policy/manifest -> implementation -> source audit -> tests -> generated-resource audit -> APK audit -> workflow`.

Mandatory rules:

1. **Single-source feature expectations.** Where practical, zoom/symbol/category/resource expectations are declared once in a machine-readable or importable feature policy/manifest and consumed by audits/tests. Do not maintain independent hard-coded copies merely for verification.
2. **No unconditional historical resource lists.** APK/resource audits derive required artifacts from the current active mapping. Unreferenced legacy resources may exist, but their presence must not be required unless another active path uses them.
3. **Behavioral freeze, not symbol-name freeze.** Frozen records describe accepted user behavior. Internal symbol/function names are implementation details unless technically required. An explicit user-approved behavior change updates the active expectation before build.
4. **Validator-consistency preflight is mandatory before Gradle.** The cheap preflight must execute every audit mode that can be evaluated without an APK and must additionally verify that packaged-APK expectations are derivable from the same current policy. A known stale validator blocks the build.
5. **Changed-concept sweep is a hard checklist.** For each changed concept/name/value, search implementation modules, apply scripts, tests, audits, workflow YAML, generated-resource expectations, formal/frozen docs, and obsolete legacy references before commit. Record or encode the result where practical.
6. **APK-only assertions must be minimal.** APK verification checks facts that truly require the package (ABI, package/label, signature, JNI/resource presence actually referenced by current policy). It must not introduce a second independent specification.
7. **Failure classification.** If build succeeds but validation fails, first classify whether the product is wrong or the validator is stale. Never change correct product behavior merely to satisfy a stale validator.
8. **Recurrence is a process defect.** Another stale-audit failure after this rule requires fixing the shared policy/preflight mechanism, not merely editing the newly failing line.

### Gate 1 concrete recurrence

Run `36234235991`, head `d2de8eec9f0eaa5dd754f8b0ef33945565f03d11`:
- Gradle build succeeded.
- arm64/AArch64, package `jp.cb6.navi`, and label `CB6 Navi` passed.
- final APK audit failed only with `native symbol mapping absent: cb6-signal-s`.
- Root cause: the user-approved 200m change made z15 use `cb6-signal-xs`, but APK verification still required the old unconditional `xs/s/m/l` native symbol set.

The correction for Gate 1 must remove the duplicated historical requirement and make the APK audit derive the required native symbols from the active zoom/symbol mapping. Do not restore the larger 200m symbol merely to satisfy the old audit.
