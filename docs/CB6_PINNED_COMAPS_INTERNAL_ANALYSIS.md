# Pinned CoMaps Internal Analysis Record

Analysis baseline: `comaps/comaps@7113ccb5f086183f8884b2aa4e58c987466b6704`
Date recorded: 2026-09-25
Scope: internal source tracing for CB6-relevant systems. This supplements `CB6_COMAPS_ARCHITECTURE.md` with concrete pinned-source findings.

## 1. Framework is the central native composition root

Pinned `libs/map/framework.hpp` shows `Framework` owns or coordinates:
- `FeaturesFetcher` / `DataSource`;
- `SearchAPI`;
- `DrapeEngine`;
- `Storage`;
- `BookmarkManager`;
- `SearchMarks`;
- `RoutingManager`;
- traffic, transit and isolines managers;
- viewport and current model view.

Constructor order is intentional. `FeaturesFetcher.InitClassificator()` occurs before displayed categories/search setup. Search is initialized before bookmark callbacks are wired. Bookmark changes feed SearchAPI. Routing receives the BookmarkManager. This means feature data, search, bookmarks and routing are not independent Android subsystems; they converge in native Framework.

`Framework::OnViewportChanged` propagates viewport changes to SearchAPI, BookmarkManager, TrafficManager, TransitReadManager and IsolinesManager.

CB6 rule: before introducing a parallel Android-only data model, determine whether Framework/DataSource already exposes the needed information.

## 2. MWM type creation is explicit and stable

Pinned `data/mapcss-mapping.csv` states:
- OSM tags are preprocessed first;
- mappings become classificator types;
- the generator C++ parser is `generator/utils.cpp::ParseMapCSS()`;
- the style compiler uses `tools/kothic/src/libkomwm.py::komap_mapswithme()`;
- the runtime renderer does not read mapcss-mapping.csv directly; it consumes generated `data/types.txt`;
- feature-to-OSM conversion exists in `editor/feature_type_to_osm.cpp`;
- types with no style can be discarded unless retained by `indexer/feature_visibility.cpp::IsUsefulNondrawableType()`.

Concrete pinned type IDs relevant to CB6:
- `amenity|fuel` = 67
- `amenity|hospital` = 114
- `aeroway|aerodrome` = 136
- `shop|supermarket` = 160
- `shop|convenience` = 161
- `highway|motorway` = 58
- `highway|motorway_link` = 44

Therefore convenience stores are definitely native MWM feature types in this pinned baseline.

## 3. Brand and operator survive into feature metadata/search

Pinned source proves brand/operator are first-class feature metadata:
- `libs/indexer/feature_meta.hpp`: `FMD_OPERATOR=6`, `FMD_BRAND=30`.
- `generator/osm2meta.cpp`: validates/stores operator and brand.
- `generator/feature_builder.cpp`: deduplicates brand metadata when appropriate.
- `generator/search_index_builder.cpp`: indexes operator and localized brands.
- `libs/search/ranker.cpp`: uses operator and brand when scoring names.
- `libs/search/intermediate_result.cpp`: reads `FMD_BRAND` and translates it.
- `libs/map/place_page_info.cpp`: reads both operator and brand.
- Android metadata enum also exposes FMD_OPERATOR and FMD_BRAND.

Important qualification: feature_builder may drop redundant brand metadata in cases where brand duplicates feature names; brand availability must therefore be tested on actual Japanese MWM examples rather than assumed for every store.

CB6 consequence: a native-MWM brand-icon solution is technically plausible. It must first prove that enough Japanese convenience features retain usable brand/operator/name identity at runtime. If brand metadata is absent, name/operator can be controlled fallbacks.

## 4. Current vehicle-style behavior explains the screenshots

Pinned `data/styles/vehicle/include/Icons.mapcss` includes `shop=convenience` only in a generic text-label rule at high zoom (`node|z18-[shop=convenience]` grouped with POIs using `text: name`). It does not provide CB6 brand-specific convenience icon selection.

This matches the observed CB6 screenshot: stock text such as "セブン-イレブン" can appear while no CB6 brand icon appears.

Pinned default style also has generic `shop=convenience` styling at lower zoom than vehicle style. Theme/mode therefore materially changes POI visibility.

CB6 consequence: for convenience stores, modifying the native style pipeline is a stronger long-term candidate than duplicating every store over Overpass, but MapCSS alone cannot branch on FMD_BRAND unless that metadata is exposed to style selectors. We must not assume it is. Two safe native options require further proof:
1. classify selected brands into dedicated classificator subtypes at generation time and style those types; or
2. extend rule/feature processing to expose brand identity to symbol selection at runtime.
Option 1 affects map generation/map compatibility; option 2 affects renderer/indexer code. Existing downloaded maps constrain the choice.

## 5. Search path

Pinned Android JNI `android/sdk/src/main/cpp/app/organicmaps/sdk/search/SearchEngine.cpp` calls native `Framework->GetSearchAPI()`. Interactive search invokes viewport search and, when requested, everywhere search. Results cache FeatureID and center; result conversion returns FeatureID/type/address/name to Java.

Pinned `libs/search/engine.hpp/.cpp` is the underlying search engine layer. Search indexes include operator/brand metadata during generation.

CB6 rule: voice/fuzzy normalization should continue feeding stock SearchEngine. Do not create a CB6 POI search database.

## 6. Routing path

Pinned `libs/map/routing_manager.hpp/.cpp` is Framework's route coordinator. It owns route-session behavior and consumes DataSource/CountryInfo/BookmarkManager. Android `Framework.java` exposes route build/follow, route points, route steps, saved route points and auto-reroute through JNI.

CB6 free-expressway work must trace native road/toll attributes through routing, not filter displayed roads or Android search results.

## 7. Bookmark/favorites path

Pinned `libs/map/bookmark_manager.hpp` is native bookmark state. Framework wires bookmark create/update/delete/attach/detach callbacks into SearchAPI.

Pinned Android JNI `bookmarks/data/BookmarkManager.cpp`:
- loads bookmarks through native BookmarkManager;
- creates/deletes categories/bookmarks;
- creates a bookmark from current PlacePage information;
- stores feature types into bookmark data when selected object is a feature;
- supports preparing KML/KMZ-like files for sharing;
- exposes category visibility/sorting/search.

CB6 sync consequence: future phone<->CB6 favorites synchronization should operate on native bookmark/category identity and serialized bookmark data, not scrape UI labels.

## 8. Location/camera path

Framework receives user position and updates:
- BookmarkManager MyPositionMark;
- elevation position when relevant;
- RoutingManager current position;
- TrafficManager current position.

Viewport changes fan out to multiple managers. Android's location state and CB6 MwmActivity changes therefore sit above a shared native state.

CB6 rule: car-position lowering should use supported viewport/routing offset behavior where possible; do not move the underlying GPS coordinate merely to change screen placement.

## 9. UserMark internals and the current convenience failure

`libs/map/user_mark.hpp/.cpp` defines UserMark types/groups and DebugMarkPoint. The mark type is set by constructor and group operations act on that type.

CB6 JNI rebuilds a mark group with ClearGroup/SetIsVisible/CreateUserMark/NotifyChanges. Therefore a `Cb6ConvenienceMark : DebugMarkPoint` constructed with the default DebugMarkPoint constructor belongs to DEBUG_MARK even if the publishing function is conceptually "CB6 driving".

This exactly explains why a synthetic convenience probe can fail while traffic signals remain visible through their separately proven path.

Current correction: convenience marks explicitly use `DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING)`. This must be real-device validated before freezing.

## 10. Rendering/style generation

Runtime map rendering does not directly interpret source MapCSS. Source style is compiled/generated. Consequently every style change must verify:
- mapping/classificator if type semantics change;
- active default and vehicle `Icons.mapcss`;
- light/dark source SVG;
- symbol generation/atlas;
- generated drules;
- overlay priority/collision;
- actual APK payload.

The build's `configure.sh` generation stage can rewrite resources. CB6 intentionally reapplies runtime-sensitive patches after configure.

## 11. Practical architecture decision for convenience stores

Evidence now establishes:
A. Native MWM definitely contains `shop=convenience`.
B. Brand/operator are supported metadata and participate in search/place-page.
C. Vehicle style currently displays generic convenience text rather than CB6 brand icons.
D. Existing downloaded MWM compatibility matters; changing generator classifications alone would require regenerated maps and is therefore not automatically the safest solution.
E. Current supplemental Overpass/UserMark path can work without map regeneration but duplicates native data and adds network/state/group failure modes.

Decision gate before replacing current supplemental path:
1. Add/read-only diagnostic capable of inspecting nearby native convenience FeatureIDs and their name/brand/operator metadata on the existing Japanese MWM.
2. Measure representative 7-Eleven, FamilyMart, Lawson, Seicomart, MyBasket, Ministop, Daily Yamazaki records.
3. If identity is reliably available from existing MWM, implement brand icon rendering from native features without Overpass.
4. If not reliable, retain supplemental acquisition only for missing identity/data and avoid duplicate stock labels.
5. No wholesale generator/classificator change unless compatibility with already-downloaded maps is explicitly accepted.

This is the safest path because it proves the data available on the user's actual map before selecting implementation architecture.

## 12. Internal subsystem index for future work

Data generation:
- `generator/`
- `generator/osm2type.cpp`
- `generator/osm2meta.cpp`
- `generator/feature_builder.cpp`
- `generator/search_index_builder.cpp`

Feature/index:
- `libs/indexer/`
- `libs/indexer/feature_meta.*`
- `libs/indexer/brands_holder.*`
- `libs/indexer/feature_visibility.cpp`

Map/application:
- `libs/map/framework.*`
- `libs/map/place_page_info.cpp`
- `libs/map/user_mark.*`
- `libs/map/bookmark_manager.*`
- `libs/map/routing_manager.*`

Search:
- `libs/search/engine.*`
- `libs/search/ranker.cpp`
- `libs/search/intermediate_result.cpp`
- Android JNI `android/sdk/src/main/cpp/app/organicmaps/sdk/search/SearchEngine.cpp`

Styles/render:
- `data/mapcss-mapping.csv`
- `data/styles/default/include/`
- `data/styles/vehicle/include/`
- `libs/drape/`
- `libs/drape_frontend/`

Android/native bridge:
- `android/sdk/src/main/java/app/organicmaps/sdk/Framework.java`
- `android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp`
- bookmark/search/routing JNI directories
- app UI under `android/app/src/main/java/app/organicmaps/`

## 13. Analysis completeness statement

This record covers the complete CB6-relevant architectural surfaces and concrete pinned-source call/data paths needed for planned work. It is not a claim that every line in the multi-million-line upstream repository has been manually annotated. "Complete internal analysis" for engineering purposes means every CB6-relevant subsystem has a documented ownership/path and future modifications must drill into the exact call chain before editing.

Any newly discovered internal dependency must be added here and to the change-impact map in the same development cycle.
