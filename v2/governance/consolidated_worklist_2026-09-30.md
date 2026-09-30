# CB6 Consolidated Governance / Discussion / Continuing Worklist — 2026-09-30

Status: CONSOLIDATED WORKLIST — classification/status index, not replacement authority
Basis HEAD: `81d3fd73c329a7c6fc443c60b9751912c51cf4ea`

## Purpose
- Merge the previously discussed **議論リスト**, **継続リスト**, and the confirmed contents of `v2/governance/session_summary_2026-09-30.md`.
- Remove duplicate development work.
- Mark items already implemented separately from items still requiring discussion, mechanism work, or Evidence.
- Existing ACTIVE authority remains authoritative; this file does not silently replace or activate rules.

## Status legend
- **実施済み**: mechanism/authority already exists and no duplicate redevelopment is required.
- **一部実施**: meaningful mechanism exists, but the consolidated requirement is not fully closed.
- **未実施**: no sufficient mechanism/Evidence confirmed.
- **議論継続**: policy semantics still need explicit discussion/decision before implementation.
- **確定要件**: user confirmed on 2026-09-30 that the session-summary contents are to be incorporated.

## Deduplicated list

1. **GitHub latest HEAD as canonical state / chat is not Evidence** — **実施済み・確定要件**
   - Covers continuing-list Method/Evidence authority and discussion-list repository reconstruction aspects.
   - Existing root invariants and governance already establish repository authority.

2. **Optimistic concurrency: start HEAD vs pre-push HEAD; stale work must resync** — **一部実施・確定要件**
   - Session summary requires it; audit checklist C-01..C-03 also requires it.
   - Operational practice exists, but dedicated fail-closed enforcement for C-02/C-03 remains unconfirmed.

3. **Method / Build / Behavior judgments and Evidence remain separate** — **実施済み**
   - Duplicate redevelopment not required.

4. **Acceptance Criteria / final acceptance Evidence chain** — **一部実施**
   - APK/device/independent-review chain is mechanically checked.
   - Explicit sealing of acceptance criteria to target version/basis HEAD remains to be fully confirmed.

5. **Operational Rule Registry / Rule Coverage / future continuing-rule intake** — **実施済み**
   - ACTIVE rules are machine-covered; PROPOSED rules are excluded from coverage.

6. **Meta-Verifier / verifier connection / duplicate or zero connection detection** — **実施済み**
   - Existing workflow/meta and verification-mechanism checks cover the core requirement.

7. **Destructive / fail-closed tests** — **実施済み**
   - Existing governance mechanisms include destructive tests; new mechanisms must continue to add them.

8. **Progress reporting uses exactly three operational classes: 進めて推奨 / 待ち / スマホ操作が必要** — **一部実施・確定要件**
   - Protocol and PROPOSED registry entry exist.
   - Contract/verifier/destructive test/Gate Evidence/adoption/MACHINE_ENFORCED coverage are still incomplete.

9. **Meaning of 進めて推奨** — **確定要件 / mechanism pending**
   - Safe assistant/GitHub-side work continues; chat-instruction waiting alone is not a reason to stop.

10. **Meaning of 待ち** — **確定要件 / mechanism pending**
    - Must identify approximate wait time, next check timing, and whether non-conflicting work can continue.
    - Read-only/static/Evidence work may continue during external waits.

11. **Meaning of スマホ操作が必要** — **確定要件 / mechanism pending**
    - Use only when physical CB6/device action or Evidence is actually required; specify the action/Evidence needed.

12. **Progress-query stale-state resynchronization** — **実施済み＋確定要件**
    - Old notification/report is not authority.
    - On progress inquiry, current HEAD/Run and material raw logs/Evidence must be freshly obtained.

13. **Specific approval before implementation-problem fix** — **実施済み＋確定要件**
    - `OPS-USER-APPROVAL-BEFORE-FIX-001` is ACTIVE/MACHINE_ENFORCED.
    - Missing, post-hoc, reused, or mismatched approval fails closed.

14. **Define the authority of a generic “進めて” separately from exact fix approval** — **一部実施 / 議論継続**
    - Exact-fix approval cannot be replaced by an old generic “進めて”.
    - Broader semantics of “進めて” across investigation, governance work, build, and other actions still need explicit classification.

15. **Separate investigation permission from modification/fix permission** — **一部実施 / 議論継続**
    - Fix boundary is protected by approval rule.
    - General action-classification contract is not yet complete.

16. **Classify user statements: question / investigation request / progress permission / fix approval / specification decision / continuing rule / stop-resume instruction** — **議論継続**
    - Needed so a statement cannot silently gain stronger authority than intended.

17. **Separate fact / inference / proposal in discussion and decision records** — **議論継続**
    - No complete machine-enforced mechanism confirmed.

18. **Detect and resolve user/assistant interpretation mismatch before promotion to authority** — **議論継続**
    - No complete mechanism confirmed.

19. **Separate discussion / agreed decision / implementation permission / ACTIVE governance state** — **一部実施 / 議論継続**
    - Governance adoption lifecycle already separates PROPOSED→verified→ACTIVE.
    - A generic discussion-state model covering all user instructions is not yet complete.

20. **Repository-only reconstruction of current instructions, agreements, pending items, and permissions across new chats** — **一部実施**
    - Root reconstruction exists.
    - Discussion/session operational state is not yet fully represented in reconstruction outputs.

21. **Prove discussion completion before Governance promotion** — **議論継続**
    - Governance lifecycle exists after a candidate is defined, but discussion-completion evidence itself is not fully specified.

22. **Governance adoption conditions and Governance self-verification** — **実施済み**
    - Method revision lifecycle, independent review, destructive verification, adoption and refreeze path exist.
    - Do not duplicate this mechanism unless a demonstrated gap requires revision.

23. **Evidence Inventory and Evidence basis HEAD** — **一部実施**
    - Inventory/classification exists.
    - Per-Evidence basis HEAD requirement from audit checklist E-02 is not generally enforced.

24. **Monitoring cycle / liveness ledger** — **未実施 to required level**
    - Monitoring policy and verifier exist.
    - Empty `cycles.jsonl` can pass; unique cycle ID→basis HEAD→Actions Run→result commit/no-commit Evidence and fail-closed liveness remain incomplete.

25. **GitHub Actions scheduled monitoring Evidence** — **一部実施**
    - Hourly workflow exists.
    - Durable cycle ledger linkage and proof that scheduled runs leave the required Evidence remain incomplete.

26. **Method Freeze / formal Method revision procedure** — **実施済み**
    - Frozen authority and formal candidate→verification→independent review→adoption→refreeze sequence exist.

27. **Current-head CB6 real-device investigation method** — **一部実施**
    - Device Evidence machinery exists.
    - Diagnostic path requirement remains: source→classification→presentation/UserMark/native path→Drape/render→visibility/zoom→screen, identifying the first zero point before a fix.

28. **Diagnostic/logcat Evidence boundary** — **一部実施**
    - Requirement exists in audit checklist.
    - Generic machine enforcement of “only necessary diagnostics” and real-device/logcat cause acceptance is not complete.

29. **Rollback traceability** — **未実施 to required level**
    - Must record implementation-start HEAD, change commit/files, and recovery method; dedicated enforcement remains unconfirmed.

30. **Independent final acceptance review** — **実施済み**
    - Existing rule and final-acceptance chain cover the requirement; duplicate redevelopment not required.

31. **Signal-side read-only constraint during current Governance/HEAD-integrity work** — **確定要件 / current operational constraint**
    - Signal code/style/patch must not be changed while this constraint applies.
    - Signal investigation may use objective GitHub Evidence and must locate the first zero point through input→patch→generated output→runtime.

32. **Actions result handling** — **確定要件 / partly existing practice**
    - Success requires Artifact/Evidence inspection.
    - Failure requires raw-log cause analysis.
    - An approved fix follows minimal change→Gate→HEAD recheck→commit/push→rebuild.

33. **Previously adopted Governance V3 remains adopted during safe HEAD/push holds** — **確定要件 / already reflected operationally**
    - A temporary commit/push hold caused by inability to prove the correct HEAD does not cancel prior adoption.

## Removed duplicates / no redevelopment
The following earlier list topics are retained through the canonical item above and must not be developed twice:
- Notification stale-state → item 12.
- Approval / approval reuse / post-hoc approval / generic old approval → items 13–15.
- Rule Registry + Rule Coverage + future rule intake → item 5.
- Meta-Verifier + Gate connection checks → item 6.
- Fail-closed/destructive testing → item 7.
- Method/Build/Behavior separation → item 3.
- Method Freeze → item 26.
- Independent review → item 30.
- HEAD authority → items 1–2.
- Signal investigation and read-only policy → items 27, 31.
- Progress three-class reporting → items 8–11.

## Remaining development priority
1. Complete the three-class status-reporting mechanism (items 8–11) without duplicating stale-state or approval mechanisms.
2. Define the user-statement/action authority model (items 14–21).
3. Close concurrency enforcement (item 2).
4. Close Evidence basis-HEAD enforcement (item 23).
5. Close monitoring cycle/liveness and scheduled-run Evidence (items 24–25).
6. Close rollback enforcement (item 29).
7. Close remaining real-device diagnostic Evidence mechanism gaps (items 27–28).
8. Re-run cross-coverage audit so every unresolved item is either mechanically enforced or explicitly remains discussion/proposed.

## Preservation rule
- Existing implemented mechanisms are reused rather than redeveloped.
- A PROPOSED/discussion item must not be silently treated as ACTIVE.
- Any change to frozen Method authority must follow `v2/gates/method_revision_procedure_v1.json`.
- This consolidated list does not itself activate a rule or authorize a feature-code fix.
