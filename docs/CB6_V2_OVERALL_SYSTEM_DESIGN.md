# CB6 Navi V2 — Overall System Design

Status: CANONICAL V2 DESIGN
Baseline: `comaps/comaps@7113ccb5f086183f8884b2aa4e58c987466b6704`
Target: ATOTO CB6 / Android 13 / arm64-v8a
Design principle: preserve CoMaps, extend minimally, keep CB6 responsibilities isolated.

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
