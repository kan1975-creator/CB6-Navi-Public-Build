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
| Traffic signals | Frozen CB6 migration on CoMaps UserMark path | TODO | TODO | TODO if dynamic annotation pattern relevant | TODO only if graph semantics relevant | Run #65 behavior fixed; compare only for architecture/regression lessons |
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
