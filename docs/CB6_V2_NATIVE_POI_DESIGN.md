# CB6 V2 Native MWM Feature Access and POI Classifier Design

Status: PRIOR DETAILED DESIGN INPUT — NOT IMPLEMENTATION AUTHORITY DURING OVERALL DESIGN REBUILD\n\nThis document remains evidence for the rebuilt design. Its former implementation-ready status is suspended until the rebuilt overall design consumes the active requirements and revalidates this subsystem.
Upstream: `comaps/comaps@7113ccb5f086183f8884b2aa4e58c987466b6704`

## 1. Purpose

Provide one read-only native interface for CB6 to inspect nearby features already present in downloaded MWM maps, then classify them into stable CB6 POI identities. This becomes shared infrastructure for convenience stores, fuel stations and major facilities.

It must not create a second POI database and must not require network access.

## 2. Proven upstream API path

Pinned source provides:
- `Framework` owns `FeaturesFetcher`.
- `FeaturesFetcher::ForEachFeature(rect, fn, scale)` delegates to `EditableDataSource::ForEachInRect`.
- `FeatureType` exposes `GetID()`, `GetCenter()`, `ForEachType()`, names, and metadata.
- metadata exposes `FMD_OPERATOR` and `FMD_BRAND`.
- classificator exposes `GetTypeByPath(...)`.

Therefore V2 can inspect nearby native features without search queries, Overpass or generated fake marks.

## 3. Native domain types

V2 introduces a small CB6-owned native domain, conceptually:

`Cb6PoiRecord`
- stable runtime FeatureID identity;
- Mercator center;
- category enum;
- brand enum;
- default/localized display name evidence;
- raw brand/operator evidence for diagnostics;
- source = NativeMwm.

`Cb6PoiCategory`
- Convenience
- Fuel
- MajorFacility
- Unsupported

`Cb6PoiBrand`
- SevenEleven
- FamilyMart
- Lawson
- Seicomart
- MyBasket
- Ministop
- DailyYamazaki
- Other
- Unknown

Brand enum can be extended for fuel later without changing feature-access API.

Production renderer consumes normalized enums, not raw strings.

## 4. Query API

Native query contract:

`QueryCb6Pois(center, radiusMeters, categoryMask, limit)`

Rules:
- construct Mercator rectangle from center/radius;
- use `FeaturesFetcher::ForEachFeature` at an appropriate detailed scale;
- reject features outside requested radius after rectangle iteration;
- classify types first, before reading expensive names/metadata;
- return only requested categories;
- deterministic nearest-first result order;
- hard result cap;
- no mutation of DataSource, bookmarks, search or renderer;
- no network call.

Initial diagnostic radius: 2500 m.
Production radius is owned by presentation/use case and is not hard-coded into feature access.

## 5. Type matching

Resolve required classificator types once after classificator initialization, never by numeric ID literals in production code.

Required paths:
- `shop|convenience`
- `amenity|fuel`
- selected major-facility types as their specs are frozen.

Feature type comparison uses classificator type semantics. The documented numeric IDs are evidence only, not implementation constants.

## 6. Name and metadata evidence

For matching features, collect:
1. FMD_BRAND when present;
2. FMD_OPERATOR when present;
3. localized/preferred feature name;
4. default feature name;
5. all-name fallback only for diagnostics/classification when necessary.

No user-visible convenience label is implied by collecting names; names are identity evidence.

## 7. Shared brand normalization

Normalization is centralized and deterministic:
- Unicode/case/spacing/punctuation normalization suitable for Japanese/Latin brand aliases;
- exact canonical aliases preferred;
- conservative substring fallback only for known unambiguous aliases;
- priority: brand metadata -> operator -> names;
- preserve evidence source for diagnostics.

Examples to support after evidence confirmation:
- 7-Eleven / セブン-イレブン variants
- FamilyMart / ファミリーマート
- Lawson / ローソン
- Seicomart / セイコーマート
- MyBasket / まいばすけっと
- Ministop / ミニストップ
- Daily Yamazaki / デイリーヤマザキ

Do not classify an unknown store into a known brand merely to obtain an icon. Unknown maps to generic.

## 8. Android/JNI boundary

Production POI rendering should remain native where possible. Android does not need every nearby static POI every location tick.

A development-only JNI diagnostic endpoint may return compact text/records for real-device evidence:
- FeatureID printable identity;
- category;
- distance;
- chosen brand enum;
- evidence source;
- name/brand/operator values.

This endpoint is guarded by a CB6 diagnostic/build flag and is not a production acquisition loop.

## 9. Renderer boundary

Feature access/classification does not decide how icons are drawn.

The renderer receives:
- FeatureID/center;
- category/brand enum;
- zoom presentation policy.

This allows the later evidence-based choice between:
A. native feature/style extension;
B. native overlay associated with existing MWM FeatureID.

External Overpass UserMarks are not part of the primary static POI architecture.

## 10. Duplicate/label policy

One native MWM feature corresponds to one CB6 static POI presentation record.

For convenience:
- CB6 brand icon is allowed;
- stock convenience text must be suppressed according to formal spec;
- suppression must target convenience presentation only, not globally remove names from unrelated POIs.

No native + Overpass duplicate is permitted unless a specifically documented fallback gap requires it.

## 11. Cache/update design

Native feature records are derived from installed MWM and need no persistent duplicate database.

Runtime cache key includes:
- map/data generation identity as available;
- query region;
- category mask.

Invalidate/requery when:
- movement exits configured query reuse radius;
- relevant map registration/deregistration changes;
- presentation category requirements change.

Do not poll MWM on a network-style timer.

## 12. Threading

Feature iteration executes on a native context compatible with DataSource access. Results are immutable snapshots before crossing to another component/thread.

Renderer update is separate and atomic.
Android main thread never performs a large MWM rectangle scan.

## 13. Diagnostic evidence plan

Before convenience renderer implementation, a diagnostic APK must collect representative real MWM records around the device.

For each detected convenience store record:
- distance;
- FeatureID;
- type matched;
- preferred/default name;
- FMD_BRAND;
- FMD_OPERATOR;
- normalized brand result and evidence source.

Acceptance for native brand classification:
- representative known brands around test area are found from installed map;
- false-brand classification = 0 in inspected sample;
- missing metadata can fall back to name/operator without losing known stores;
- no network is needed.

If evidence is insufficient, record exactly which identity is missing before designing a supplemental path.

## 14. Performance limits

Initial diagnostic:
- radius 2500 m;
- type-first filtering;
- hard cap 300 matching POIs;
- nearest-first final output.

Production rendering queries only categories required by current CB6 presentation. Instrument query duration during development. A performance regression is not accepted merely because output is correct.

## 15. Safety/regression invariants

This module:
- does not touch Run #65 signal acquisition/rendering;
- does not call `nativeSetCb6DrivingMarks`;
- does not clear UserMark groups;
- does not modify search history/results;
- does not modify routing;
- does not mutate bookmarks;
- does not require map regeneration;
- does not require internet;
- does not fabricate POIs.

## 16. Planned source ownership

V2 consolidated implementation should use responsibility-owned files rather than numbered patch history. Target conceptual locations:
- native CB6 POI query/classifier under map/application integration;
- narrow JNI diagnostic bridge under Android SDK bridge;
- Android diagnostic logger/view only when diagnostic build flag is enabled;
- tests/audits under V2-specific validation.

Exact file names are chosen when implementing against the clean pinned tree; the ownership boundaries above are fixed.

## 17. Tests before APK build

Native/unit/static tests:
- classificator paths resolve;
- type filter accepts convenience and rejects unrelated shop;
- each canonical brand alias normalizes correctly;
- unknown remains generic/unknown;
- priority brand > operator > name;
- distance/cap ordering deterministic;
- no UserMark/group APIs referenced by feature-access module.

Generated-tree preflight:
- no Overpass endpoint in static POI module;
- no numeric type-ID dependency;
- diagnostic JNI is build-flag guarded;
- signal files unchanged relative to the chosen frozen migration stage.

## 18. Implementation gate

Do not implement final convenience rendering until the native MWM diagnostic evidence is collected on CB6. The query/classifier infrastructure itself may be implemented after Gate 0 build is reproducible because it is read-only and isolated.
