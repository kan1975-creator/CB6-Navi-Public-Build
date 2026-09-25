# CB6 Navi V2 Baseline

Status: ACTIVE SECOND-GENERATION DEVELOPMENT
Started: 2026-09-25
Branch: `cb6-v2-clean`

## Purpose

CB6 Navi V2 resets implementation debt, not product requirements. The old `clean-import` branch remains a reference/baseline and must not be destroyed.

## Authoritative upstream baseline

CoMaps commit:
`7113ccb5f086183f8884b2aa4e58c987466b6704`

V2 implementation must be reconstructed deliberately from that pinned baseline. The historical CB6 patch stack is reference material only; it is not the V2 architecture.

## Mandatory reading before implementation

- `docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md` — canonical V2 whole-system design and module/dependency contract

- `docs/CB6_COMAPS_ARCHITECTURE.md`
- `docs/CB6_PINNED_COMAPS_INTERNAL_ANALYSIS.md`
- `docs/CB6_CHANGE_IMPACT_MAP.md`
- `docs/CB6_FROZEN_FEATURES.md`
- `docs/CB6_KNOWN_FAILURES_AND_PROCESS.md`

## Build gates

V2 proceeds in gates. A later gate must not be treated as complete until the previous gate has evidence.

### Gate 0 — clean reproducible baseline
- Checkout exact pinned CoMaps commit.
- Apply only minimum CB6 identity/build configuration required for an installable CB6 package.
- No traffic signals, convenience, stop, GS, facility or experimental POI patches.
- Generate/configure resources.
- Build release arm64-v8a APK.
- Verify APK integrity, package id and arm64 native libraries.
- Real-device launch check on CB6.
- Record exact upstream SHA, workflow SHA, APK hash.

### Gate 1 — frozen traffic signal port
- Port only the minimum implementation needed to reproduce the real-device accepted Run #65 signal behavior.
- Do not redesign signal behavior.
- Compare 200m/500m behavior against frozen acceptance record.
- Freeze V2 signal implementation after real-device acceptance.

### Gate 2 — native MWM convenience diagnostic
- Read nearby native `shop=convenience` FeatureIDs from the existing downloaded map.
- Record type/name/brand/operator for representative Japanese brands.
- Diagnostic must be read-only and development-only.
- Do not choose the final renderer/data source until evidence is collected.

### Gate 3 — convenience architecture decision and implementation
Preference order:
1. existing native MWM/core path;
2. minimal native extension;
3. isolated CB6 implementation;
4. external network supplement only for proven gaps.

## V2 structural rule

Do not recreate the historical chronological `apply_cb6_*.py` stack. V2 code is organized by responsibility:
- baseline/build/identity
- map data and POI
- rendering
- location/camera
- routing/navigation
- search/voice
- UI/settings
- audits/tests

A temporary migration script is allowed only when it is idempotent, owned by one responsibility, and cannot silently overwrite another subsystem.

## Completion authority

GitHub Actions success proves build integrity only. Real-device CB6 behavior is the final feature acceptance authority.


## Overall-design gate

No V2 feature implementation may bypass `docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md`. If detailed evidence changes a design decision, update the overall design + impact map in the same development cycle before implementation. Open evidence gates are not permission to guess.
