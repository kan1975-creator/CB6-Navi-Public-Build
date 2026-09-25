# CB6 Change Impact Map

Use this before editing. "Primary" means expected implementation area; "must inspect" means a change is incomplete until those layers are checked.

| Feature | Primary path | Must inspect before build | Real-device acceptance |
|---|---|---|---|
| Traffic signals | Supplement acquisition + JNI/UserMark | Java scheduler/parser, retained dataset, JNI, UserMark group, symbols, zoom, final workflow ordering, signal audits | Existing frozen 200m/500m behavior unchanged |
| Convenience stores | Prefer MWM/style if feasible; current supplemental path | OSM/MWM type/brand availability, Java acquisition/parser, JNI, CB6_DRIVING group, symbol atlas, zoom, label suppression, stock duplicate POI, final generated tree | Brand icon visible; no convenience text; correct zoom scaling |
| Fuel stations | Prefer stock MWM/style | mapping/classificator, vehicle Icons.mapcss, symbols, priority/collision, labels | Visible at specified scales without duplicate network POIs |
| Major facilities | Stock MWM/style | classificator, vehicle/default style, priorities, labels, scale visibility | Required facilities visible/readable without overlap regression |
| Stop signs | Supplemental/directional candidate | acquisition, heading/distance filter, retained marks, JNI/group, symbol zoom | Only intended forward/relevant stops |
| Own position | stock location/render + Android offset | MwmActivity, LocationState, native my-position, routing offset, heading/camera | correct lower position, no rotation-axis shift, stable stop behavior |
| Compass/heading | location sensors + camera | Android sensor/location, heading transition, native follow mode, compass UI | heading accurate; north lock toggle correct |
| Road-name HUD | routing/address -> Android UI | RoutingInfo.currentStreet, fallback address, layout/orientation, lifecycle | current road readable and positioned correctly |
| Voice search | Android speech -> stock SearchEngine | permission, on-device recognizer, fallback intent, normalization, history, stock result selection | Japanese voice reaches normal CoMaps results |
| Fuzzy search | normalization -> stock SearchEngine | keyboard/voice/show-on-map paths, history, result routing | aliases work without separate search behavior |
| Free expressway only | routing engine | MWM toll/access attributes, vehicle model, route options, persistence/UI, route tests | toll sections excluded; genuinely free motorway sections allowed |
| Toll fee display | route + external/embedded fee model | route segments, vehicle class, fee source/versioning, UI, offline/update policy | displayed fee traceable and correct for selected route |
| Favorites sync | stock bookmark storage | bookmark IDs/storage, KML, update metadata, conflict resolution, local Wi-Fi transport | bidirectional item-level sync without destructive overwrite |

## Cross-cutting impact checks

Every rendering change: default + vehicle styles, light + dark symbols, generated atlas/drules, zoom, collision/priority, final APK payload.

Every Java/JNI change: Java declaration/call, JNI signature, native implementation, thread/lifecycle behavior, retained state, group clearing/visibility.

Every patch-script change: all later scripts, configure-generated files, audits, workflow grep/invariants, final generated tree.

Every data-source change: offline availability, cache/update policy, duplicate features, failure behavior, privacy/network load.

## High-risk coupling already observed

- `nativeSetCb6DrivingMarks` replaces/clears a mark group; partial publishers must preserve unrelated marks.
- Signal-only refresh can erase convenience/stop marks unless datasets are merged.
- A DebugMarkPoint-derived class inherits its mark type from the constructor; the wrong type places it in the wrong group.
- Resource generation can overwrite patched style/symbol state.
- Later apply scripts can restore obsolete behavior after an earlier correct patch.


## Architecture decision gate for native POIs

Before adding/retaining an external POI source for data already present in MWM, inspect the actual existing-map FeatureID metadata (type/name/brand/operator). For convenience stores, this read-only diagnostic is required before choosing native style/render extension versus supplemental Overpass marks.
