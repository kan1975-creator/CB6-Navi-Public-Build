# CB6 Gate Coverage Audit

Status: ACTIVE
Date: 2026-09-26

## Scope checked

Repository tree was inspected for build workflows and V2 control surfaces.

V2 workflows on `cb6-v2-clean`:
- build_cb6_v2_baseline.yml — gate enforced before build
- build_cb6_v2_identity.yml — gate enforced before build
- build_cb6_v2_signals.yml — gate enforced before build
- cb6_development_gate.yml — gate self-test and negative test

Legacy workflow:
- build_cb6_voice_final.yml triggers only on `clean-import` and `cb6-runtime-final`; it is not a `cb6-v2-clean` build entry point. It remains historical/legacy and must not be used as V2 authority.

## Fail-closed evidence

After gate wiring, all three V2 build workflows were triggered and all three stopped at the first `Enforce CB6 development gate` step while the project state is `OVERALL_DESIGN_REBUILD`:
- Clean Baseline run 36238794998 — expected failure at gate
- Gate 0B Identity run 36238797943 — expected failure at gate
- Gate 1 Signals run 36238799927 — expected failure at gate

No Java setup, dependency install, CoMaps clone, transform, build or APK packaging step ran after the gate failure.

The standalone development-gate workflow succeeded on the same repository state (for example run 36238799887), proving that the gate itself recognizes the rebuild state while feature-build requests are denied.

## Holes found and closed in this pass

1. Initial gate was documentation plus a standalone workflow; existing V2 build workflows could still run. Closed by putting the verifier immediately after checkout in every V2 build workflow.
2. Initial future implementation gate had no per-feature identity. Closed by requiring `--feature=<gate-id>` and a future `v2/gates/features/<gate-id>.json` record once implementation is enabled.
3. A build could otherwise claim generic implementation permission. Closed by requiring design section, impact check, repo-sweep declaration, audits, tests and implementation-enabled stage in each future feature record.
4. Gate behavior could be assumed rather than tested. Closed by a negative test that deliberately requests a blocked/missing feature build.
5. Old overall design could silently regain authority. Verifier fails unless the retired design remains marked `RETIRED AS CANONICAL`.

## Deliberately still closed

There are currently no feature gate records and `feature_builds_allowed=false`. This is intentional. They must not be created as implementation-enabled records until the rebuilt overall design is evidence-complete and verified.

## Remaining classes that cannot be honestly called closed yet

These are not permission bypasses in the current V2 build path; they are completion work for the design rebuild:
- evidence inventory must be completed and reconciled;
- web/external evidence gaps must be refreshed;
- rebuilt overall design needs a canonical machine-readable trace;
- feature gate records must be generated from that verified design;
- validator expectations should be derived from shared current specification data where feasible, eliminating duplicated hard-coded values such as the stale signal-symbol failure;
- all future V2 workflows must be covered automatically, so adding a new workflow without the gate becomes a failing repository check.

Until those are implemented and negative-tested, project state stays `OVERALL_DESIGN_REBUILD` and V2 feature builds remain blocked.
