# CB6 V2 Cross-Project Comparison Matrix

Status: MANDATORY ENGINEERING INPUT
Projects: CoMaps / OsmAnd / Vela / MapLibre Navigation / Valhalla

## Rule

Before implementing a major V2 feature, complete its row with source-backed implementation findings. The purpose is to identify proven patterns while keeping CoMaps as the CB6 base. A useful pattern may be adapted; another project's architecture is not automatically imported.

Decision priority:
`CoMaps native > minimal CoMaps extension > isolated CB6 implementation > external/network supplement`.

## Matrix

| CB6 feature | CoMaps | OsmAnd | Vela | MapLibre Navigation | Valhalla | CB6 decision status |
|---|---|---|---|---|---|---|
| Native POI / convenience / GS / facilities | Analysis started: MWM FeatureType + metadata + styles | TODO source trace | TODO source trace | N/A unless renderer/location integration relevant | N/A for static POI rendering | Native MWM diagnostic required before renderer choice |
| Traffic signals | Frozen CB6 migration on CoMaps UserMark path | Route data has explicit traffic-signal and directional signal rules | Regional on-device road-feature dataset with signal/stop kinds and road bearing; Overpass only fallback | Navigation symbols are separately owned; overlap/placement can be explicitly controlled | N/A for CB6 signal rendering; routing graph semantics only, so no engine dependency | DESIGN-COMPLETE for migration architecture; Run #65 visual/behavior remains frozen |
| Stop signs | Detailed source/design pending | TODO | TODO | TODO | TODO | Not selected |
| Own position / camera / heading | Framework/location path mapped | TODO | TODO | TODO | N/A except map matching | Not selected |
| Low-speed stability / map matching | Existing CoMaps location/routing path to trace deeper | TODO | TODO | TODO | TODO Meili/map matching | Not selected |
| Road-name / navigation HUD | Routing/address state identified | TODO | TODO | TODO | TODO maneuver output relevance | Not selected |
| Search / fuzzy / voice | Stock SearchEngine is mandatory output | TODO | TODO | N/A/limited | N/A | Keep one CoMaps search engine; normalization details pending |
| Navigation session / reroute | RoutingManager path identified | TODO | TODO | TODO | TODO | Not selected |
| Free expressway / toll avoidance | Native routing attributes must be traced | TODO | TODO | TODO request/cost model | TODO dynamic costing | Not selected |
| Toll fee display | No guessed fee | TODO | TODO | TODO | TODO | Authoritative Japan fee model unresolved |
| Offline/update model | CoMaps downloaded MWM authoritative | TODO | TODO | TODO | TODO tiled graph/update lessons | Native/offline-first fixed |
| Favorites / phone sync | BookmarkManager authoritative | TODO | TODO | N/A | N/A | Last priority; transport/conflict details pending |

## Evidence format

For each completed comparison add a section below containing:
- repository/project and exact source version/commit where practical;
- files/classes/modules inspected;
- data ownership;
- update/lifecycle model;
- rendering or routing integration;
- offline behavior;
- strengths applicable to CB6;
- incompatibilities/risks;
- selected CB6 pattern;
- rejected alternatives.

## Initial external-project observations

These are orientation only and do not complete any matrix row.

### Vela
Public project documentation describes separation of open map/place data, offline region support and turn-by-turn navigation, with a technical SPEC as its source of truth. Its module/data separation and driving UX are useful comparison targets. CB6 must not inherit Vela's optional Google-web data behavior because CB6's normal navigation must remain free/offline and CoMaps-based.

### MapLibre Navigation
The project separates navigation core from UI and exposes replaceable location/routing integration. This is useful for evaluating CB6's module boundaries and navigation UI separation, but CB6 already has a native CoMaps renderer/routing stack and should not replace it merely to match MapLibre.

### Valhalla
Valhalla separates graph data, dynamic costing, map matching, path generation and maneuver narration into distinct modules. It is especially relevant when comparing free-expressway/toll policy, map matching and routing-cost architecture. It is not a reason to replace CoMaps routing without a demonstrated requirement.

## Completion policy

A row becomes DESIGN-COMPLETE only after the comparison evidence is recorded and the selected CB6 approach is reflected in:
- `CB6_V2_OVERALL_SYSTEM_DESIGN.md`;
- `CB6_V2_MODULE_CONTRACTS.md` when boundaries change;
- `CB6_CHANGE_IMPACT_MAP.md`;
- feature-specific detailed design.

Real-device acceptance remains separate from design completion.


## Traffic signals — comparison evidence and V2 decision

Status: DESIGN-COMPLETE for architecture. This comparison does **not** reopen the accepted Run #65 visual behavior.

### CoMaps / CB6 baseline
- Base: pinned CoMaps `7113ccb5f086183f8884b2aa4e58c987466b6704`.
- Existing accepted CB6 behavior is documented in `CB6_V2_TRAFFIC_SIGNAL_MIGRATION.md`: real signals only, scale-dependent symbols, forward-only enlargement, nearest-first cap, and independent Dynamic Road Marks ownership.
- V2 must migrate the proven behavior without importing the chronological V1 patch stack.

### OsmAnd
- Inspected OsmAnd commit `7771d5addbafd71f98fb73eac9fa6343b68d7993`.
- `RouteRegion.kt` reserves routing rules for `highway=traffic_signals`, `traffic_signals:direction=forward/backward`, stop and give-way controls.
- `RouteTypeRule.kt` promotes `highway=traffic_signals` to a dedicated routing type rather than treating it as arbitrary UI text.
- Applicable lesson: road controls should be typed data with direction semantics available near the routing/data layer. CB6 should not infer all signal semantics in Android UI code.

### Vela
- Inspected Vela commit `b5643ca16e9b01e5b14db661f77ce7a086598353`.
- `scripts/road_features_tsv.py` extracts traffic signals, stops, crossings, traffic calming and cameras into a compact regional dataset and can attach undirected road bearing.
- `RoadFeatures.kt` loads regional road-control data once, spatially indexes it locally and uses Overpass only as fallback when no regional dataset covers the location.
- Applicable lesson: for a Hokkaido-only product, a compact offline regional road-control index is a viable fallback architecture if the native CoMaps/MWM path is proven insufficient. It is superior to making routine live Overpass queries.
- Rejected for first signal migration: replacing the already accepted Run #65 acquisition source at the same time as moving to V2. Source migration and visual migration must not be coupled.

### MapLibre Navigation
- Inspected MapLibre Navigation commit `f9b73d16f4228050fe0fe6aa93be46a3fe36673a`.
- `NavigationSymbolManager.java` owns navigation symbols separately and explicitly controls overlap/placement.
- Applicable lesson: dynamic road-control symbols require their own lifecycle/ownership and explicit collision policy. This reinforces the V2 rule that a signal publisher cannot clear convenience/fuel/facility/stop state.
- MapLibre's renderer is not imported; CoMaps remains the renderer.

### Valhalla
- N/A for the signal **display** implementation. Valhalla's graph/costing architecture is relevant to routing policy and map matching, but adding a Valhalla dependency provides no justified benefit for reproducing the frozen CB6 signal overlay.
- Revisit only if a future routing feature needs signal-aware costing or map matching.

### Selected CB6 V2 structure
1. Keep Dynamic Road Marks as the sole owner of signal presentation state.
2. Use typed immutable signal snapshots and a narrow acquisition-provider interface.
3. Preserve Run #65 scale, forward-cone, distance, refresh and nearest-first behavior exactly for the first V2 migration.
4. Keep rendering collision/placement policy explicit and independent from static POI rendering.
5. Do not allow any publisher to clear another road-mark or POI family.
6. After frozen behavior is reproduced on CB6, separately investigate native Hokkaido MWM/route-control availability.
7. If native MWM is insufficient, prefer a Hokkaido offline regional road-control index patterned after the proven regional-data approach before relying on routine network queries.
8. Overpass remains a fallback/evidence source, not the long-term preferred dependency for Hokkaido operation.

### Rejected approaches
- importing the old V1 patch sequence;
- changing signal source and renderer simultaneously during the frozen migration;
- sharing a mutable mark group with convenience/GS/facilities;
- replacing CoMaps renderer or router with MapLibre/Valhalla solely for signal display;
- permanent live-Overpass dependence when an offline Hokkaido data path can be proven.
