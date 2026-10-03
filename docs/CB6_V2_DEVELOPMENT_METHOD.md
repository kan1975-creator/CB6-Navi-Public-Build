# CB6 V2 Development Method

Status: ACTIVE / MACHINE-ENFORCED
Machine authority: `v2/gates/development_method_contract.json`

## Purpose
Prevent recurrence of previously identified causes by making the development sequence executable and fail-closed rather than dependent on chat memory or manual discipline.

## Mandatory sequence
1. Read current CB6 requirement/authority.
2. Analyze the exact pinned CoMaps source before implementation.
3. Research official/upstream/web information when external API, data model, platform, OSM, or upstream behavior is material.
4. Treat web findings as research only; revalidate them against the pinned CoMaps source.
5. Record research in `v2/gates/research_records/<feature>.json`.
6. Complete Change Impact and repository-wide sweep before implementation.
7. Change implementation and its audit/validation together.
8. Run positive tests and an audit-specific destructive/fail-closed proof.
9. Pass the per-feature Gate.
10. Build from the exact pinned CoMaps commit.
11. Verify APK evidence.
12. Verify CB6 real-device evidence before acceptance/freeze.

A failure returns work to the earliest affected stage. No later stage may waive an earlier failure.

## Original CoMaps source rule
Every feature must record:
- repository: `comaps/comaps`;
- exact pinned commit: `7113ccb5f086183f8884b2aa4e58c987466b6704`;
- concrete original CoMaps source paths inspected;
- findings derived from those paths.

CB6-side files alone do not satisfy original-source analysis.

## Authority rule
Web pages, historical CB6 documents, old implementations, and old validators are not automatically current authority. Retired/revalidation-required evidence cannot be promoted directly into a feature contract. Current CB6 authority and the pinned source must resolve implementation decisions.

## Change rule
Unrecorded specification changes and unrelated behavior changes are forbidden. When a specification change is technically required, record its reason, affected domains, authority/requirement update, audit/test changes, and expected real-device effect before implementation.

## Audit rule
An audit file existing is not proof. Every feature audit requires a feature-specific executable destructive proof. Correct implementation must never be changed merely to satisfy a stale validator; the validator and its authority must be corrected together.

## Completion rule
Planning/documentation is not implementation evidence. Commit is durable change; successful Gate is method evidence; APK evidence is build evidence; CB6 real-device acceptance is behavioral completion.

## Mechanical enforcement
`verify_project_integrity.py` locks the method contract itself.
`verify_project_gate.py` enforces research, impact, authority, audit proof, and feature state.
`test_gate_fail_closed.py` destructively tests global method invariants.
`test_feature_gate_contract.py` destructively tests per-feature bypasses.
Feature workflows must run the feature Gate before build and preserve the gated control state.
