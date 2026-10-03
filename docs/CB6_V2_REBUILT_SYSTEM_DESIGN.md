# CB6 V2 Rebuilt System Design

Status: candidate canonical design; implementation remains blocked until authority/traceability activation is completed.
Pinned upstream: CoMaps `7113ccb5f086183f8884b2aa4e58c987466b6704`.

## Design authority and boundaries

This design is rebuilt from active decisions plus active evidence. Retired/historical documents are not independently authoritative. CoMaps owns standard search, routing, BookmarkManager, offline maps, Framework/DataSource and normal map rendering. CB6 extends only explicitly required behavior. Preferred implementation order is native CoMaps/MWM capability, minimal native extension, isolated CB6 implementation, then justified network supplementation. Workflow ordering and generated resources are part of the architecture.

## PROCESS

Requirements: `PROC-001`, `PROC-002`.

GitHub is the persistent source of truth. Active decisions, authority, evidence, impact records and feature gates are fail-closed. No feature build is permitted while OVERALL_DESIGN_REBUILD is active. Implementation requires repository-wide integrity, per-feature impact review, gate stamp, APK evidence, CB6 device evidence and final acceptance.

## SIGNAL

Requirements: `SIG-200M-001`, `SIGNAL-ZOOM-001`.

Traffic-signal presentation is owned by the dedicated signal path, not a shared destructive POI group. Current display authority is current_spec.json. Signals are not required at 1 km. At the 200 m driving presentation they remain slim and approximately the accepted 500 m visual size; forward/near emphasis may use only the explicit current-spec mapping. Historical symbol sizes are evidence, not authority.

## SIG

Requirements: `SIG-COVERAGE-001`, `SIG-UPGRADE-001`.

Acquisition must cover highway=traffic_signals and crossing=traffic_signals so non-intersection and otherwise missed signals are included. Acquisition/cache/JNI/render ownership stays isolated. Acceptance requires both clean-install and update-install CB6 tests; build success alone never freezes signal behavior.

## PRODUCT

Requirements: `PRODUCT-BASE-001`, `SCOPE-HOKKAIDO-001`.

Pinned CoMaps is the upstream product base and its standard routing, search, bookmarks, offline maps and place behavior remain authoritative unless an active CB6 requirement explicitly extends them. Operating and validation focus is Hokkaido; behavior outside Hokkaido may remain compatible but must not silently redefine the validation scope.

## MAP

Requirements: `MAP-CAMERA-001`, `MAP-SCALE-001`, `MAP-LABEL-001`, `VEHICLE-ICON-001`.

Driving mode follows heading by default with a north-lock toggle. Screen placement may lower the vehicle presentation but must never alter geographic GPS coordinates. Initial scale is 200 m, automatic scaling is not introduced, and user scale is persisted. Address clutter is suppressed through style/label policy while road names and major labels remain scale/collision aware. The accepted/original vehicle icon is immutable unless a later explicit vehicle-icon requirement changes it.

## HUD

Requirements: `HUD-ROAD-001`.

The bottom road-name HUD consumes existing routing/current-street or address state; it does not create a parallel road database. It defines fallback when no road is resolved and survives orientation/activity lifecycle changes.

## POI

Requirements: `POI-CONVENIENCE-001`, `POI-FUEL-001`, `POI-MAJOR-001`.

Static POIs prefer the native MWM/classificator/style path when actual pinned-map metadata proves sufficient. Convenience stores use brand icons without convenience-store text clutter; fuel and major facilities use scale-aware icon/label priority. Network duplication is a fallback only when native data is demonstrably insufficient. All paths verify default/vehicle styles, light/dark symbols, generated atlases/drules and collision behavior.

## STOP

Requirements: `STOP-001`.

Stop signs are independent dynamic road-control data. Their publisher/mark ownership must not clear signals or static POIs. Only relevant signs ahead of the vehicle are shown using explicit distance and heading filtering, with acquisition completeness and CB6 driving verification.

## SEARCH

Requirements: `SEARCH-VOICE-001`, `SEARCH-FUZZY-001`, `SEARCH-HISTORY-001`.

Voice and fuzzy/alias normalization are input layers only; all normalized queries feed the stock CoMaps SearchEngine. Japanese voice prefers on-device recognition where available and has a safe Android fallback. Keyboard, voice and show-on-map share normalization semantics. Search history and registered-item deletion operate through CoMaps-owned search/bookmark data rather than a parallel store.

## ROUTING

Requirements: `ROUTING-FREE-001`.

Free-expressway-only behavior, if enabled, belongs inside native route calculation semantics using proven toll/access attributes. Post-filtering a completed route is prohibited. Existing CoMaps route options and route result ownership remain intact.

## TOLL

Requirements: `TOLL-001`, `TOLL-ROUTE-001`.

Exact toll display is blocked until an authoritative, traceable passenger-car fee model is established. The model must bind fee to each route candidate, represent genuinely free candidates/sections as 0 yen, and define source version, update and offline behavior. Road class alone is never treated as an exact fee source.

## FAVORITES

Requirements: `FAVORITES-001`.

BookmarkManager remains the authority. Future phone-to-CB6 synchronization uses item/category identity, explicit conflict handling and non-destructive merge semantics; UI text scraping or whole-collection overwrite is prohibited.

## LIFECYCLE

Requirements: `LIFECYCLE-001`.

Startup, activity restart, theme/orientation restart and return from auxiliary navigation restore current-location/follow presentation and retained CB6 state. Navigation handoff/return behavior is tested on the actual Android lifecycle; unsupported OS guarantees are documented rather than simulated.

## UI

Requirements: `UI-LAYOUT-001`, `ORIENTATION-001`.

Driving controls retain compass upper-left with north-lock toggle, scale below with tap-to-show +/- controls, current-location lower-left and settings lower-right. Full-map tap may hide search/menu without disabling current-location access. Auto, portrait and landscape modes preserve controls and road HUD.

## LOCATION

Requirements: `LOCATION-STABILITY-001`.

Raw location, map-matched presentation and screen offset are separate concepts. Matching must not rewrite the underlying GPS observation. Heading source and low-speed hysteresis prevent rotation-axis shift, stationary jitter and false driving motion. Real-device tests cover stop/start, low speed and heading transitions.

## GOOGLE

Requirements: `GOOGLE-MAPS-001`.

Google Maps is an auxiliary handoff, not a paid map dependency or replacement navigation core. CB6 remains the intended return app after supported arrival/restart/return flows, but Android behavior that cannot be guaranteed is explicitly scoped and verified on CB6.

## CAMERA

Requirements: `CAMERA-FIXED-001`.

The accepted fixed driving-camera behavior is preserved. No unrelated feature may introduce automatic camera/scale changes. Camera changes require explicit impact review across location, follow mode, routing offset, orientation and lifecycle.

## OFFLINE

Requirements: `OFFLINE-FREE-001`.

Core navigation and static-map capability remain usable through CoMaps offline maps without paid Google/Mapbox API registration. External services may supplement dynamic or insufficient data but cannot become the sole source for core static POIs.

## CONVENIENCE

Requirements: `CONVENIENCE-BRANDS-001`.

Brand classification covers 7-Eleven, FamilyMart, Lawson, Seicomart, MyBasket, Ministop and Daily Yamazaki plus a generic fallback. Evidence priority is usable native brand metadata, then operator/name fallback, then a justified supplemental source. Historical numeric IDs are not design authority.

## Verification and release boundary

Every feature follows: active requirement → architecture ownership → Change Impact record → repository sweep → Feature Gate → gate stamp → implementation/generated-tree audit → arm64 APK build → APK byte/hash evidence → CB6 Android 13 device evidence → Final Acceptance. Clean build or GitHub Actions success is never sufficient evidence of feature completion. Unrelated CoMaps behavior must remain unchanged and regressions against known historical failures are mandatory.
