# CB6 Navi V2 — Overall System Design (RETIRED CANONICAL)

Status: RETIRED AS CANONICAL — REBUILD REQUIRED (2026-09-26)
Baseline: `comaps/comaps@7113ccb5f086183f8884b2aa4e58c987466b6704`
Target: ATOTO CB6 / Android 13 / arm64-v8a
Design principle: preserve CoMaps, extend minimally, keep CB6 responsibilities isolated.

> **DO NOT USE THIS FILE AS AN IMPLEMENTATION AUTHORITY.** On 2026-09-26 the user ordered the overall design to be rebuilt because the previously agreed development process was not executed consistently. This document is preserved only as historical input so useful prior work is not lost. New implementation decisions must come from the rebuilt design after re-verifying user decisions, pinned CoMaps source analysis, web/external-source findings, cross-project evidence, CB6 real-device evidence, known failures, and frozen/preserved behavior.


## 1. Product boundary

CB6 Navi V2 is a driving-focused extension of CoMaps. CoMaps remains authoritative for offline maps, map downloads, search result selection, routing session, route history/options, bookmarks/favorites and core location state unless a CB6 specification explicitly extends presentation or behavior.

CB6 code must not create parallel replacements for capabilities CoMaps already owns.

## 2. Layer ownership

### A. Upstream core — preserve
Foundation/platform/indexer/search/routing/storage/drape/map Framework and normal bookmark/search/routing state remain upstream-owned.

### B. CB6 native extension
Only capabilities that need native feature access, renderer integration, route semantics or camera integration live here. APIs are narrow and feature-oriented; Android must not know renderer internals.

### C. CB6 Android orchestration
Owns Android lifecycle, voice input, user settings, CB6 UI controls and requests into native APIs. It does not own an alternate map/search/routing database.

### D. Generated resources
MapCSS, SVG, symbol atlas and drawing rules are treated as generated build inputs. Source and generated-output invariants are audited together.

### E. Diagnostics/tests
Development-only diagnostics expose evidence without changing production map behavior. Diagnostics are removable/disabled for release.

## 3. Module plan

Implementation boundaries are mandatory in `docs/CB6_V2_MODULE_CONTRACTS.md`.


| Module | Responsibility | Primary data | Output | Must not own |
|---|---|---|---|---|
| V2 Baseline | reproducible pinned source/build/identity | pinned SHA | verified arm64 APK | feature behavior |
| Native POI Access | query nearby MWM features/metadata | DataSource/FeatureID | typed POI records | network acquisition |
| POI Presentation | CB6 visibility/icon/label policy | native POI records | map overlays/style | search database |
| Dynamic Road Marks | signals/stops/dynamic marks only | feature-specific source | isolated driving overlays | static MWM POIs when native data suffices |
| Location/Camera | screen offset, follow/heading/north lock | stock location state | viewport behavior | modified GPS coordinates |
| Road HUD | current road presentation | stock routing/address state | bottom road-name UI | separate geocoder |
| Search/Voice | normalization + speech input | Android speech/text | stock SearchEngine query | separate search engine |
| Routing Policy | CB6 route-option extensions | native route graph/attributes | route constraints | UI-only filtering |
| Toll Information | fee association/display | proven fee model + selected route | fee UI | inferred fee from road class |
| Favorites | stock bookmarks; later sync adapter | BookmarkManager data | standard favorites + sync | label-scraping database |
| UI/Settings | controls/layout/preferences | settings + module state | CB6 driving UI | core navigation state |

## 4. Static POI architecture

Detailed contract: `docs/CB6_V2_NATIVE_POI_DESIGN.md` is mandatory for native MWM feature access and shared POI classification.



Convenience stores, fuel stations and major facilities follow one shared architecture.

1. Query/identify existing MWM feature.
2. Read type + FeatureID + center + localized/default name + brand + operator where available.
3. Normalize identity in a CB6 POI classifier.
4. Apply presentation policy by category/brand/zoom.
5. Render through the least invasive native path compatible with existing downloaded maps.
6. Suppress/alter stock text only where the formal CB6 spec requires it.
7. External acquisition is a fallback for proven MWM gaps, not the default.

The classifier is shared infrastructure. Convenience, fuel and facilities must not each invent independent name matching.

### Convenience policy
No convenience text. Brand icon only.
Target brands: 7-Eleven, FamilyMart, Lawson, Seicomart, MyBasket, Ministop, Daily Yamazaki, generic fallback.
Scale policy: ~1 km very small, ~500 m small, ~200 m standard.
Final rendering mechanism is gated by actual Japanese MWM metadata evidence.

### Fuel policy
Use native MWM `amenity=fuel` first. Brand-specific rendering may use the same classifier if metadata is sufficient. Exact brand set/zoom presentation is to be frozen only after representative MWM inspection.

### Major facilities
Use native MWM categories. Facility name visibility is scale-aware and collision-aware. Large landmarks may receive higher presentation priority, but must not globally disable collision handling.

## 5. Traffic signals — frozen migration design

Traffic signals are a migration, not a redesign. V2 ports the minimum Run #65 accepted behavior into an isolated Dynamic Road Marks module.

Invariants:
- 200 m accepted standard size;
- ~500 m smaller/thinner;
- not required at 1 km;
- forward/near behavior retained;
- accepted acquisition timing/radius/cap retained.

The V2 signal module must not share a destructive whole-group publisher with static convenience/fuel/facility POIs. A future stop-sign publisher must also be isolated or merged through an explicit typed registry.

## 6. Stop signs

Stop signs are directional driving information, not ordinary static POI presentation. Design:
source -> typed stop record -> distance/heading relevance filter -> Dynamic Road Marks renderer.
Only relevant forward stops within the specified distance window are presented. Exact source and thresholds remain a detail-design gate; no fabricated stop positions.

## 7. Location, car position and camera

Stock GPS/location is immutable truth. Screen placement never changes geographic coordinates.

Pipeline:
Android/stock location -> Framework/location state -> routing position -> camera/follow policy -> screen-space own-position offset.

Required behavior:
- startup focuses current position;
- driving orientation is not accidentally forced north-up;
- north-lock toggle is explicit;
- own-position is lower on screen;
- rotation pivot remains visually stable;
- stopped-position jitter is filtered only at presentation/heading policy, not by inventing movement;
- previous manual scale is preserved where specified; no unwanted auto-scale.

## 8. Compass and heading

Heading source selection and confidence are separate from camera mode. Compass UI reflects actual mode and heading state. Tapping toggles north-lock/follow-heading without rewriting location.

Sensor/GPS heading transitions require hysteresis/filtering so stopped or low-speed noise does not spin the map.

## 9. Road-name HUD

Preferred source is current routing/current-street state. When not navigating, use an existing native address/road lookup if available; do not create a separate online geocoder.

HUD is a presentation component with portrait/landscape layout rules. It must not interfere with current-location/settings controls.

## 10. Search and voice

One search engine only: stock CoMaps SearchEngine.

Pipeline:
keyboard or Japanese speech -> CB6 normalization/alias layer -> stock SearchEngine -> stock results -> stock place page/history/routing.

Voice input is an Android input method, not a second POI source. Permission/recognizer failure falls back cleanly to text search.

## 11. Routing extensions

CB6 route policy extends native routing options; it does not post-filter a completed route on Android.

### Free expressway sections only
Required semantics: avoid toll sections while permitting genuinely free motorway/expressway sections.
Design gate:
OSM/MWM toll/access metadata -> routing feature/edge semantics -> vehicle model/route options -> persisted CB6 option -> route calculation -> UI.
Road class alone is insufficient.

### Toll fee display
Eligibility and fee calculation are separate. Fee display must be traceable to a reliable Japan fee data model/source and selected route. Until that source/model is proven, no guessed price is shown.

## 12. Favorites/bookmarks and later phone sync

CoMaps BookmarkManager remains authoritative. V2 preserves standard favorites first.

Later bidirectional phone/CB6 sync operates on bookmark/category identity + update metadata, not visible labels. Preferred transport is local connectivity available during smartphone tethering. Conflict handling is item-level and must never replace the whole collection destructively.

This remains last priority.

## 13. UI layout ownership

Driving screen components are independent presentation units:
- compass: upper left;
- scale: below compass;
- scale tap reveals +/- controls;
- current-location: lower left;
- settings: lower right;
- road-name HUD: bottom;
- map tap can enter uncluttered/full-map presentation as specified.

UI components call module APIs. They do not directly mutate native engine internals.

## 14. State and persistence

Separate:
1. CoMaps-owned state: maps, routes/history where standard, bookmarks, search history.
2. CB6 preferences: north lock/follow mode preference, last manual scale, layout/orientation choices, POI display choices, route extensions.
3. transient runtime state: heading confidence, diagnostic counters, temporary overlay records.

CB6 preferences use one versioned settings namespace. No feature stores duplicate copies of stock CoMaps state.

## 15. Lifecycle and recovery

Activity recreation/theme/orientation changes must restore presentation state without resetting core navigation. Process restart must recover supported CoMaps route/navigation state before CB6 presentation is attached.

Google Maps helper integration is an external handoff, not the CB6 navigation state owner. Return/restart behavior must be implemented explicitly and tested independently.

## 16. Threading and update model

- UI work: Android main thread.
- native map mutations: use upstream-required engine/thread boundary.
- network/diagnostics: background executor.
- immutable typed snapshots cross module boundaries.
- one feature update cannot clear another feature's state.
- schedulers are feature-specific; rendering commits are typed/atomic.

## 17. Error/fallback behavior

Offline is normal, not an error. Native map/search/routing must continue without CB6 network supplements.
Missing optional metadata -> generic category identity, not disappearance.
Missing external supplement -> retain native data.
Renderer/resource mismatch -> fail preflight/build, not silently ship.
Diagnostic failure -> no production UI change.

## 18. Build architecture

V2 does not reuse the chronological legacy patch stack.

Pipeline:
1. checkout V2 control repo;
2. clone exact pinned CoMaps;
3. verify pristine SHA/tree;
4. apply consolidated responsibility-owned V2 modules;
5. configure/generate resources;
6. apply only explicitly documented post-generation transforms if unavoidable;
7. inspect final generated tree;
8. run spec/regression audits;
9. build arm64 release;
10. inspect APK/package/native ABI/resources;
11. real-device acceptance;
12. freeze accepted feature.

Goal: post-generation transforms trend toward zero.

## 19. Audit architecture

Audits are divided into:
- baseline provenance;
- frozen-feature regression;
- module boundary/invariant;
- generated resource;
- package/ABI;
- obsolete legacy flow;
- real-device acceptance checklist.

Audits must not require arbitrary historical function names. Any audit that conflicts with current formal specification is updated before build rather than forcing obsolete code back in.

## 20. Development-only observability

Each new data/render feature gets temporary evidence at boundaries:
- number of source features found;
- number classified by category/brand;
- number submitted to renderer;
- symbol/category chosen;
- rejection reason where useful.

Diagnostics contain no fabricated production POIs and are disabled/removed after acceptance.

## 21. Dependency order

Foundation dependencies:
V2 baseline -> native feature access -> shared POI classifier -> POI presentation.

Feature order:
1. Gate 0 pristine/reproducible build.
2. Minimal CB6 identity/build shell.
3. Frozen traffic-signal migration and acceptance.
4. Native MWM POI diagnostic + shared classifier.
5. Convenience stores.
6. Fuel stations.
7. Major facilities.
8. Stop signs.
9. Location/camera/compass.
10. Road-name HUD and driving-screen layout.
11. Search normalization + voice.
12. Routing extensions: free expressway policy.
13. Toll-fee model/display after data source proof.
14. Google Maps handoff/recovery hardening.
15. Favorites phone sync last.

Independent design work may proceed in parallel, but integration follows dependency gates.

## 22. Definition of done for every feature

A feature is complete only when:
- formal specification is linked;
- architecture path and impact map are updated;
- no obsolete legacy path remains active;
- source syntax/static checks pass;
- generated-tree invariants pass;
- frozen features are unchanged;
- arm64 APK/package checks pass;
- CB6 real-device acceptance passes;
- acceptance evidence/version is recorded in frozen-features record.

## 23. Open design gates — evidence required, not guesses

These are known design decisions intentionally not fabricated:
- actual brand/operator/name availability for representative Japanese convenience/fuel MWM features;
- exact native rendering hook that best preserves existing downloaded-map compatibility for brand icons;
- stop-sign data completeness and directional semantics in the installed map/source;
- exact low-speed heading confidence thresholds after CB6 sensor/GPS observation;
- Japanese toll-edge representation in the pinned routing graph;
- authoritative/updatable toll-price data model;
- bookmark sync transport/protocol details.

These gates do not block the overall architecture. They block only the affected detailed implementation until evidence exists.

## 24. Non-negotiable regression boundaries

- Preserve CoMaps standard functionality unless explicitly extended.
- Preserve frozen Run #65 traffic-signal behavior.
- No external network dependency for normal offline navigation.
- No parallel search engine.
- No mutated GPS coordinate for visual offset.
- No whole-group overlay clear that erases unrelated features.
- No guessed toll fees.
- No destructive whole-list favorites synchronization.
- No return to a long chronological legacy patch stack.


## 25. Cross-project implementation comparison — MANDATORY

Before detailed implementation of each major CB6 feature, compare how the same or closest problem is solved in these open-source projects:
- CoMaps — authoritative implementation base for CB6.
- OsmAnd — mature offline navigation/POI/routing reference.
- Vela — modern Android/MapLibre driving UI, POI and offline/navigation reference.
- MapLibre Navigation — navigation-core/UI separation, location and navigation-session reference.
- Valhalla — routing graph, costing, map matching and maneuver-generation reference.

This comparison is an engineering input, not permission to copy architectures wholesale. CoMaps compatibility and the CB6 formal specification remain authoritative.

### Required comparison record per feature

For every major feature, record:
1. how CoMaps currently implements the relevant data/state/render/routing path;
2. how OsmAnd approaches the equivalent problem;
3. how Vela approaches it;
4. how MapLibre Navigation approaches it, where applicable;
5. how Valhalla approaches it, where applicable;
6. strengths, risks, dependencies, offline behavior and map-data compatibility of each approach;
7. the selected CB6 V2 structure and why it fits the existing CoMaps baseline;
8. approaches explicitly rejected and why.

### Features requiring comparison

At minimum:
- convenience stores / fuel / major-facility POIs;
- traffic signals and directional stop information;
- own-position rendering, heading, camera/follow mode and low-speed stability;
- road-name/navigation HUD and driving UI;
- text/fuzzy/voice search integration;
- rerouting and navigation-session lifecycle;
- free-expressway/toll avoidance semantics;
- toll-fee presentation architecture;
- offline behavior/data updates;
- bookmarks/favorites and eventual phone synchronization.

### Selection rule

Use the comparison to learn proven patterns, then choose in this order:
1. existing CoMaps native mechanism;
2. minimal extension of CoMaps native mechanism;
3. isolated CB6 implementation compatible with CoMaps state/data;
4. external/network supplement only when native data/capability is proven insufficient.

Do not replace the CoMaps engine merely because another project has a useful implementation. Do not introduce a new dependency until its benefit and regression impact are documented.

### Development gate

A major feature cannot move from detailed design to production implementation until its cross-project comparison is recorded in the V2 comparison matrix. If a project is not applicable to a feature, record N/A with the technical reason rather than forcing a comparison.


## Proven-implementation adoption principle — MANDATORY

V2 does not optimize for the smallest source diff as an end in itself.

For each major feature, after the mandatory cross-project comparison, CB6 should actively adopt proven architecture, algorithms, state-management patterns and responsibility boundaries from mature navigation projects when they improve correctness, stability, maintainability or development speed and are compatible with the CoMaps base and applicable licenses.

Decision order:
1. reuse an already-good CoMaps implementation when it satisfies the CB6 requirement;
2. adapt a proven implementation pattern from CoMaps/OsmAnd/Vela/MapLibre Navigation/Valhalla into the corresponding CoMaps responsibility;
3. make a larger but well-isolated CoMaps extension when that is safer or cleaner than accumulating small patches;
4. use an isolated CB6-specific implementation where no compatible native structure exists;
5. use an external/network dependency only when the native/offline paths cannot satisfy the requirement.

The phrase "minimal extension" means minimum unnecessary divergence from CoMaps; it does **not** mean refusing a better proven design merely because it changes more lines.

For each adopted external pattern, record:
- the source project/version or commit where practical;
- what behavior/algorithm/module boundary is being adopted;
- why that project uses the structure;
- the corresponding CoMaps subsystem and data/lifecycle constraints;
- whether direct code reuse is license-compatible or whether only the architecture/algorithm is being reimplemented;
- integration and regression risks;
- rejected alternatives.

Never assume a foreign implementation can be transplanted unchanged. Prove compatibility at the data-model, threading/lifecycle, rendering/routing and Android boundaries, then verify by build and CB6 real-device testing.

This principle is persistent across time gaps and future tasks and must not regress to chronological one-error-at-a-time patch accumulation.


## Hokkaido-only operational optimization — MANDATORY

CB6 Navi V2 is operationally targeted at **Hokkaido, Japan only**. The upstream CoMaps worldwide-capable foundation must remain intact unless there is a separately reviewed reason to change it, but CB6-specific design, data validation, optimization, acceptance testing and information-density decisions shall use Hokkaido as the authoritative operating region.

Consequences:
- Do not spend CB6-specific complexity on worldwide edge cases that cannot occur in the intended Hokkaido operation.
- Validate native MWM classifications, brand/operator/name evidence and routing semantics against actual Hokkaido map data before adding external duplicate data paths.
- Optimize POI priorities for Hokkaido driving, including convenience stores (especially Seicomart), fuel, roadside stations, parking, toilets, hospitals, drugstores, supermarkets, home centers, airports, ferry terminals and other useful major facilities where reliable data exists.
- Investigate Hokkaido-relevant road information such as passes and seasonally restricted roads as separate evidence-gated features; do not fabricate live/seasonal state.
- Hokkaido-only scope permits richer useful information, but **information density must be scale- and context-controlled** rather than displaying everything simultaneously.
- Default presentation principle: long range shows only high-value driving landmarks; medium range progressively adds fuel/convenience/facilities; close range may add traffic signals, stops and finer road information according to each frozen/formal feature specification.
- Prefer offline/native Hokkaido MWM information. External/network data is supplemental only when native data is proven insufficient and must not make core offline navigation dependent on connectivity.
- Real-device acceptance should cover representative Hokkaido environments: Sapporo urban roads, suburban roads and longer-distance/rural driving as relevant to the feature.
- A feature need not be generalized for use outside Hokkaido unless doing so is essentially free or required to preserve CoMaps compatibility.

### Hokkaido information inventory gate

Before expanding static POI presentation, perform an evidence-based inventory of what the pinned/current Hokkaido MWM already contains for the CB6-relevant categories. Record actual type, brand, operator, name and other usable metadata from representative Hokkaido features. Use this inventory to decide what can be rendered offline, what needs classification improvements, and what truly requires supplemental data.

The product goal is therefore not minimum map information. It is **high Hokkaido driving information value with controlled visual density and reliable offline behavior**.


## 24. System-wide runtime data plane

V2 uses four distinct data planes. Feature code must declare which plane it belongs to.

1. **Authoritative offline map plane** — installed CoMaps MWM, classificator, routing graph, search index and bookmarks. This is the default source for static map/navigation facts.
2. **Driving-state plane** — stock location, heading, routing progress, current road and camera state. CB6 may derive presentation state but must not rewrite source location.
3. **CB6 presentation plane** — immutable POI and Dynamic Road Mark snapshots, zoom policy, HUD state and UI preferences. It may disappear/rebuild without corrupting authoritative data.
4. **Supplement plane** — optional external or separately packaged Hokkaido data used only for a documented native gap. Loss of this plane must not break base map/search/routing.

No module may silently promote supplement data to authoritative CoMaps state.

## 25. Hokkaido data architecture

Hokkaido is the authoritative CB6 optimization/acceptance region while the upstream CoMaps world-capable core remains intact.

Static information follows:
`Hokkaido MWM evidence -> native classification -> CB6 presentation -> documented-gap supplement only if required`.

Road-control information follows:
`native MWM/routing evidence -> Dynamic Road Marks provider -> optional compact Hokkaido offline road-control dataset -> network fallback only where justified`.

A Hokkaido information inventory is mandatory before expanding each category. The inventory records actual type, brand, operator, name and usable routing metadata for representative Hokkaido features. Candidate inventory groups include convenience stores (especially Seicomart), fuel, roadside stations, parking, toilets, hospitals, drugstores, supermarkets, home centers, airports, ferry terminals and other major driving landmarks.

Current/seasonal facts such as active closures are not inferred from static MWM. A future live-status feature requires a separately proven authoritative source, freshness model and offline fallback.

## 26. Presentation-density architecture

More Hokkaido information does not mean rendering everything simultaneously.

Presentation policy is category + zoom + driving-context based:
- long range: only high-value orientation/major-facility information;
- medium range: convenience, fuel and useful driving facilities with controlled collision;
- close range: signals, directional stops and finer road information;
- navigation-critical dynamic marks have separate collision ownership from static POIs.

Each category owns a visibility ladder. A category may reduce labels/icons at distance, but it must not globally change another category's collision policy.

## 27. Navigation state machine

CB6 UI must consume a single navigation-session state derived from CoMaps rather than independent booleans spread across screens.

Conceptual states:
`Idle -> RoutePlanning -> RouteReady -> Navigating -> Rerouting -> Arrived`, with recoverable external-handoff/process-restart transitions.

The state machine does not replace CoMaps RoutingManager. It is a narrow CB6 presentation/orchestration view of authoritative routing state. Search, HUD, camera, Google Maps handoff/recovery and route-option UI consume this view so lifecycle restoration cannot leave mutually inconsistent controls.

## 28. Location/heading confidence model

Location coordinate, movement bearing, sensor heading and camera mode are separate concepts.

The Location/Camera module will expose a derived heading state such as:
- unavailable;
- sensor-supported stationary/low-speed;
- movement-supported;
- stable fused/presentation heading.

Exact speed/accuracy/hysteresis thresholds remain evidence-gated by CB6 measurements. Camera rotation consumes the derived state; routing still consumes stock location. Screen-space own-position offset is applied only after geographic/routing position is established.

This separation is required to prevent stopped-map spin, false speed-driven heading changes and rotation-pivot drift.

## 29. Offline/update/version compatibility

Every CB6-derived cache or supplemental Hokkaido dataset must carry enough version identity to determine whether it matches the installed map/data generation.

Rules:
- never keep a derived FeatureID cache across incompatible MWM replacement;
- map registration/update invalidates affected native POI query caches;
- supplemental regional data has an explicit schema/version and atomic replacement;
- last known valid offline data may remain usable when an update check fails;
- update failure never deletes the only usable offline copy first.

## 30. Failure containment

Feature degradation is local:
- POI classifier failure -> generic/stock presentation, not map failure;
- optional road-control supplement failure -> retain proven/native/frozen path;
- voice recognizer failure -> typed search;
- toll-fee source unavailable -> route still works, fee omitted/unknown rather than guessed;
- favorites sync unavailable -> local BookmarkManager remains usable;
- Google Maps unavailable -> CB6 navigation remains usable.

A feature module must not make app startup dependent on optional network or supplemental data.

## 31. Performance budgets and scheduling policy

V2 avoids per-location-tick heavy work.

- static MWM queries use movement/region invalidation and reuse;
- dynamic road marks use feature-specific refresh/movement triggers;
- classification is type-first before expensive metadata/name extraction;
- rendering receives bounded nearest-first snapshots;
- UI thread performs no large MWM scan/network parsing;
- expensive work is observable during development with counts and elapsed time.

Exact millisecond budgets are measured on CB6 before freezing rather than guessed on desktop CI.

## 32. Compatibility and attribution gate

Before adopting external implementation code or packaged data:
- record source project/version/commit;
- record license and required attribution;
- distinguish architectural inspiration from copied/adapted code;
- prove compatibility with CoMaps/Organic Maps source and data obligations;
- preserve required user-visible attribution.

No external code/data is imported merely because its architecture is useful.

## 33. Remaining design-completion program

Overall architecture is now sufficiently fixed for implementation, but feature rows remain evidence gates. Complete them in dependency order while implementation proceeds:
1. Native POI / convenience / fuel / facilities, including Hokkaido MWM inventory.
2. Stop signs and offline Hokkaido road-control evidence.
3. Own position / camera / heading and low-speed stability.
4. Road-name/navigation HUD.
5. Search/fuzzy/voice.
6. Navigation session/reroute.
7. Free-expressway/toll avoidance.
8. Toll-fee source/model.
9. Offline/update compatibility.
10. Favorites/phone sync last.

A row may be marked DESIGN-COMPLETE only when source-backed comparison, selected CB6 structure, rejected alternatives, impact map and module-contract consequences are recorded. This prevents implementation from outrunning system design.
