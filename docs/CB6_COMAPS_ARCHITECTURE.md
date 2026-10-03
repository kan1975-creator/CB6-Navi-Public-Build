# CB6 / CoMaps Architecture Baseline

Status: canonical architecture record for CB6 development.
Pinned upstream baseline: CoMaps commit `7113ccb5f086183f8884b2aa4e58c987466b6704`.
Purpose: stop local one-line patching. Every CB6 change must be traced through the complete affected path before build.

## 1. Upstream architecture

CoMaps is a community fork in the Organic Maps family. The inherited engine is primarily C++ with Android UI/bridge code and generated map/style resources.

Layering used by the inherited core:
1. Foundation: `base/`, `coding/`, `geometry/`.
2. Platform abstraction: `platform/`.
3. Data/index: `indexer/`, `kml/`, `routing_common/`, `editor/`.
4. Domain: `search/`, `routing/`, `storage/`, `traffic/`.
5. Rendering: `drape/`, `drape_frontend/`, shaders.
6. Application aggregation: `map/`, especially Framework.
7. Android UI: `android/`; Android reaches the C++ core through JNI under `android/sdk/src/main/cpp/` and Java SDK declarations.

Primary upstream references:
- https://github.com/organicmaps/organicmaps/blob/master/docs/STRUCTURE.md
- https://github.com/organicmaps/organicmaps/blob/master/docs/STYLES.md
- https://github.com/organicmaps/organicmaps/blob/master/docs/DEBUG_COMMANDS.md
- https://github.com/organicmaps/organicmaps/blob/master/CLAUDE.md

These references explain inherited architecture. The pinned CoMaps source is authoritative when it differs.

## 2. Map-data and POI pipeline

Normal offline map feature path:
`OSM tags -> generator -> mapcss-mapping.csv / classificator -> MWM -> indexer -> drawing rules -> Drape -> screen`.

Important files/subsystems:
- `data/mapcss-mapping.csv`: OSM tag to internal feature-type mapping.
- generated `classificator.txt` / `types.txt`: internal type hierarchy.
- `generator/`: produces MWM map data.
- `indexer/`: reads/classifies map features.
- `data/styles/default/include/*.mapcss`: normal map drawing rules.
- `data/styles/vehicle/include/*.mapcss`: navigation/vehicle drawing rules.
- `priorities_4_overlays.prio.txt`: icon/caption overlay priorities.
- `data/styles/*/{light,dark}/symbols/`: source SVG symbols.
- `generate_symbols.sh`: builds symbol skins/atlases.
- `generate_drules.sh`: compiles MapCSS to drawing-rule binaries.
- `drape/` and `drape_frontend/`: actual graphics/scene/overlay rendering.

A POI may therefore exist in the MWM and search index even if its icon is hidden by style, zoom, priority or collision. Do not equate "not visible" with "not present".

## 3. Rendering and overlay pipeline

There are two materially different CB6 display paths.

### A. Stock map-feature path
MWM feature -> classificator -> MapCSS/drawing rules -> Drape overlay -> icon/label.

Use this whenever the desired information already exists in downloaded CoMaps maps and stock styling can express the required behavior. This is the preferred long-term path for convenience stores, fuel stations and major facilities if brand/type information is available at render time.

### B. CB6 supplemental UserMark path
Location/network/custom source -> Java manager -> `Framework.nativeSetCb6DrivingMarks` -> JNI `Framework.cpp` -> UserMark -> symbol name by zoom -> Drape.

Current CB6 supplemental manager:
`android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java`.

JNI bridge:
- Java declaration: `android/sdk/src/main/java/app/organicmaps/sdk/Framework.java`
- C++ implementation: `android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp`

UserMark implementation:
- `libs/map/user_mark.hpp`
- `libs/map/user_mark.cpp`

Critical invariant: UserMark **type/group is functional state**, not cosmetic metadata. A mark created in `DEBUG_MARK` is not equivalent to one created in `CB6_DRIVING`. Clear/visibility calls act by group. Any new UserMark feature must audit constructor type, ClearGroup, SetIsVisible, CreateUserMark, NotifyChanges and symbol mapping together.

## 4. Symbols and zoom

A source SVG is not sufficient by itself. Complete icon path:
`SVG -> generated symbol skin/atlas -> symbol name -> zoom mapping -> overlay placement -> screen`.

For stock POIs, MapCSS and generated drules participate. For CB6 UserMarks, `GetSymbolNames()` supplies symbol names by zoom, but the symbols still must exist in generated resources.

Upstream debugging:
- `?debug-info`: renderer/zoom/FPS information.
- `?debug-rect`: overlay rectangles; useful to distinguish rendered, collision-blocked and not-ready labels/icons.
- `?vlight`, `?vdark`: vehicle themes.

## 5. Android runtime path

`MwmActivity` is a major CB6 integration point:
- receives location callbacks,
- feeds `Cb6SupplementManager.onLocation`,
- controls startup location/heading behavior,
- road-name HUD,
- Google Maps helper,
- own-position routing offset.

Search/voice integration lives mainly in `SearchFragment.java` and `InputUtils.java`. CB6 query normalization must feed the stock CoMaps `SearchEngine`; it must not create a parallel search engine because result selection, history and routing are stock behaviors.

## 6. Routing/navigation

Core routing belongs in `routing/`; shared routing primitives in `routing_common/`. Android routing UI/controllers should be treated as consumers of the native route engine, not replacements for it.

For future "free expressway sections only" work, do not infer toll status solely from road class. First trace:
OSM/MWM toll attributes -> classificator/feature access -> routing graph/vehicle model -> route options -> Android setting persistence -> route calculation -> UI.

For future toll-price display, route eligibility and toll price are separate problems. Exact Japanese toll prices require a reliable fee data model/source; do not pretend OSM road classification alone provides exact fees.

## 7. Search

Normal path:
user text/voice -> CB6 normalization only -> stock `SearchEngine` -> result -> stock result selection/place page/routing/history.

Preserve stock search history and favorite/place behavior.

## 8. Location, heading and camera

Location is delivered on Android and consumed by both stock location state and CB6 additions. Camera/own-position behavior spans Java state plus native renderer. Before changing car position, rotation, compass or startup mode, audit:
- Android location callback/state,
- `LocationState`,
- native pending/follow mode,
- my-position rendering,
- routing offset,
- orientation/heading transition,
- activity restart/theme restart.

## 9. Favorites/bookmarks

Do not design synchronization around UI text. First trace stock bookmark storage, KML/bookmark manager, identifiers, serialization/import/export and conflict semantics. Smartphone<->CB6 sync is intentionally last priority.

## 10. Build/generation architecture

The repository is a patch/build project: GitHub Actions clones the pinned CoMaps commit and applies CB6 scripts.

Important consequence: inspecting only repository patch files is insufficient. The authoritative build input is the **generated/patched CoMaps tree immediately before Gradle build**.

Pipeline:
1. checkout CB6 repo;
2. clone pinned CoMaps;
3. apply base patch stack;
4. run CoMaps configure/resource generation;
5. reapply runtime-sensitive patches;
6. audits;
7. final proven render patches;
8. final generated-source invariants;
9. arm64 release build;
10. APK package/native verification.

A later patch can silently undo an earlier patch. Workflow ordering is therefore part of application architecture.

## 11. CB6 source-of-truth rule

For every feature:
`formal spec -> architecture path -> impact map -> repo-wide search -> patch all affected layers -> obsolete-flow check -> syntax/static audit -> inspect final generated tree -> build -> APK verification -> CB6 real-device test -> freeze`.

GitHub Actions success proves build integrity only. It does **not** prove feature completion. Real-device behavior is the final authority.

## 12. Preferred data-source rule

Before adding a network supplement, determine whether the downloaded MWM already contains the feature and needed brand/type data. If yes, prefer the native offline pipeline when it can satisfy CB6 behavior safely. Network supplemental marks are justified for data unavailable/inadequate in MWM or for genuinely dynamic data.

This rule is especially important for convenience stores, fuel stations and major facilities.


## 13. Pinned-source deep analysis

Concrete internal findings for the exact pinned CoMaps commit are maintained in `docs/CB6_PINNED_COMAPS_INTERNAL_ANALYSIS.md`. Consult it before selecting an implementation path.

## V2 signal implementation (Gate 1)

The historical shared supplemental path above is reference only for V2. Active V2 signal ownership is `SignalProvider -> immutable SignalSnapshot -> SignalController -> Framework.nativeSetCb6Signals -> CB6_SIGNAL/Cb6SignalMark`. The controller publishes on Android main and obtains network/cache data on a single worker. Group registration uses the pinned BookmarkManager's enum loop. The proven non-POI DebugMarkPoint drawing path directly batches symbols, avoiding ordinary POI/label collision without global renderer changes. One idempotent transform precedes configure; post-generation byte hashes and all atlas variants are audited. See `v2/signals/README.md`.
