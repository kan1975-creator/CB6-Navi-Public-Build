# CB6 Development Method / Independent Audit Checklist v1

Status: AGREED REQUIREMENTS SPECIFICATION — NOT IMPLEMENTATION EVIDENCE

## Audit preamble
This checklist records agreed requirements. Its presence does not mean the requirements are implemented.
Past chat claims such as completed/fixed/PASS are not Evidence.
Any SHA/commit/Run written in a request is reference information only. The reviewer MUST fetch current GitHub HEAD before judgment; current fetched HEAD wins on mismatch.

For every ID inspect: (1) existence, (2) Gate/Verifier connection including 0x/unintended duplicate connections, (3) actual/destructive execution, (4) traceable Evidence.
Allowed result states only: CONFIRMED / EXISTS_UNVERIFIED / ABSENT_OR_UNCONFIRMED.

## Method
- M-01 Separate Method / Build / Behavior judgments and Evidence.
- M-02 Method COMPLETE alone cannot make a feature COMPLETE.
- M-03 Seal Acceptance Criteria to target version/basis HEAD.
- M-04 Do not auto-reuse historical Evidence for the current version.
- M-05 Self-report/chat prose is not Evidence.\n- M-06 A new continuing operational promise remains PROPOSED unless its judgment can be derived from named GitHub repository data and machine verification. PROPOSED rules must not enter Rule Coverage or be treated as adopted mechanisms.

## Rules and Gates
- R-01 Operational Rule Registry is machine-readable authority.
- R-02 Rule Coverage links every Rule to Gate/Verifier.
- R-03 Detect zero and unintended duplicate Gate connections.
- R-04 Unknown Rule/change fails closed.
- G-01 Gate/Verifier itself is verified.
- G-02 Meta-Verifier validates existence, connection and execution.
- G-03 Destructive tests are required.
- G-04 Verifier-not-run / zero tests is not success.
- G-05 Duplicate-detection mechanism itself is Rule-Coverage protected and fail-closed.

## Notification / Evidence
- N-01 Detect Notification Stale-State.
- N-02 Notification links to actual HEAD/Evidence.
- E-01 Evidence Inventory is machine-readable.
- E-02 Evidence carries basis HEAD.
- E-03 Static/APK evidence cannot replace real-device Behavior Evidence.
- E-04 Conclusions trace to raw log/Run/commit Evidence.

## Concurrency / liveness / monitoring
- C-01 Latest GitHub HEAD is authority; there is no canonical chat.
- C-02 Optimistic concurrency compares start HEAD with pre-push HEAD.
- C-03 Stale-session push is rejected until resync.
- L-01 Unique cycle ID.
- L-02 cycle ID links basis HEAD.
- L-03 cycle ID links Actions Run ID.
- L-04 cycle ID links result commit when changed.
- L-05 No-commit requires permitted external-wait Evidence.
- L-06 Timestamp-only heartbeat is not Evidence.
- L-07 Cycle ledger actually updates; empty/disconnected ledger is detected.
- L-08 Liveness/heartbeat Gate fails closed.
- A-01 GitHub Actions cron on default branch is monitoring authority.
- A-02 Schedule must actually fire and leave Run Evidence.
- A-03 ChatGPT scheduled task is supplementary only.
- A-04 GitHub cron + ChatGPT supplementary roles remain distinct.

## Freeze / Behavior / diagnostics / rollback
- F-01 Governance expansion is frozen unless an actual gap is demonstrated.
- F-02 A real feature must pass COMPLETE; infrastructure alone is not outcome.
- B-01 Current Behavior baseline comes from current APK/new real-device Evidence; historical display claims are not current Evidence.
- B-02 Signal=0 / convenience=0 remains starting observation until new Evidence updates it.
- B-03 Standard OSM POI display is a separate fact; do not infer whole-renderer failure.
- B-04 Trace the current HEAD's actual CB6 presentation path: source -> classification -> actual UserMark/dedicated type or native path -> mark/presentation generation -> Drape/render submission -> visibility/zoom -> screen. Do not assume a single CB6_DRIVING type; signals currently use a dedicated CB6_SIGNAL type.
- B-05 Identify the first point where the count/path becomes zero before applying feature-specific fixes.
- D-01 Add diagnostic logging only at needed observation points.
- D-02 Use real-device/logcat Evidence before final Behavior-cause acceptance.
- RB-01 Record implementation-start HEAD as immutable rollback SHA.
- RB-02 Record change commit/files/recovery method.

## Independent review
- REV-01 Independent Acceptance Review is performed outside the implementation session/context. Do not supply implementation-side success claims or intent as judgment material. Judge only fixed Acceptance Criteria, freshly fetched target/current HEAD, and Evidence.
- REV-02 Independent review is required immediately before final feature COMPLETE. Its Evidence must identify feature_id, target/build commit, checklist version/path, reviewer separation, and accepted result. AI review is Evidence only; AI PASS alone never equals COMPLETE.
- REV-03 Automated independent review is deferred. If later added, it must not replace mechanical Gate, Build Evidence, or real-device Behavior Evidence.
