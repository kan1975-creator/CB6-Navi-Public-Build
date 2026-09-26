# CB6 V2 AI Development Entry Point

This file is an index, not a replacement specification.

## Mandatory first checks
1. Read `v2/gates/project_state.json`.
2. Run `python3 v2/gates/verify_project_gate.py`.
3. Run `python3 v2/gates/verify_project_integrity.py`.
4. Read active decisions from `v2/gates/active_decisions.json` and their state in `v2/gates/traceability.json`.
5. Follow `docs/CB6_DEVELOPMENT_EXECUTION_GATE.md`.

If any check fails, do not implement or build around it.

## Current authority
- GitHub branch: `cb6-v2-clean`
- Project state: machine-readable in `v2/gates/project_state.json`
- Retired overall design is historical evidence only.
- Chat memory is never sufficient authority for implementation.

## User request conversion
A normal-language user request must be converted into a durable decision before implementation:
- stable decision ID;
- requirement;
- acceptance criteria;
- affected subsystems;
- evidence references;
- traceability state.

The user does not need to specify technical impact, audits, tests, or implementation method.

## Required development chain
Requirement -> evidence -> rebuilt design -> impact -> implementation -> repository-wide sweep -> preflight -> build -> APK verification -> CB6 real-device acceptance -> freeze.

No stage may infer completion from a later stage. A successful build is not real-device acceptance.

## Change propagation
When a concept/value/name/flow changes, search and reconcile source, transforms, generated resources, tests, audits, workflows, docs, gate records, and historical assumptions. Duplicated current specification values are defects; prefer a machine-readable single source consumed by implementation validation and audits.

## Primary evidence indexes
- pinned CoMaps: `docs/CB6_PINNED_COMAPS_INTERNAL_ANALYSIS.md`
- architecture: `docs/CB6_COMAPS_ARCHITECTURE.md`
- impact: `docs/CB6_CHANGE_IMPACT_MAP.md`
- known failures: `docs/CB6_KNOWN_FAILURES_AND_PROCESS.md`
- frozen behavior: `docs/CB6_FROZEN_FEATURES.md`
- cross-project/web evidence: `docs/CB6_V2_CROSS_PROJECT_COMPARISON.md`
- gate coverage: `docs/CB6_GATE_COVERAGE_AUDIT.md`

## Product decisions
Ask the user only when a product preference/choice cannot be derived from existing authority.

## Device decisions
Ask for CB6 testing only after a specifically identified APK has passed repository, build and APK verification gates.
