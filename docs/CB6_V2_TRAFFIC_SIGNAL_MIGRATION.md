# CB6 V2 Traffic Signal Migration Design

Status: PRIOR MIGRATION DESIGN — HISTORICAL INPUT, NOT CURRENT IMPLEMENTATION AUTHORITY\n\nRun #65 remains historical real-device evidence, but later explicit CB6 requirements supersede conflicting presentation details, notably the 200 m slim-size change and V2 coverage/update-install findings.
Authority: CB6 real-device accepted Run #65 behavior

## Purpose

Move the accepted traffic-signal behavior into V2 without importing the historical chronological patch stack. This is a migration, not a redesign.

## Frozen user-visible behavior

- real traffic signals only; no synthetic intersection generation;
- hidden at the 1 km class;
- z14 / approximately 500 m: `cb6-signal-xs`, 8 x 14 SVG;
- z15 / approximately 200 m: `cb6-signal-s`, 12 x 18, accepted standard size;
- only nearby signals in the current travel direction may enlarge at closer zooms;
- forward emphasis: maximum 450 m and +/-45 degrees from current bearing;
- z17 medium, z19 large for forward emphasis;
- nearby physical signals are not intentionally dropped by ordinary POI/label collision;
- dense responses retain nearest signals before the cap;
- acquisition radius 3000 m in the frozen accepted configuration;
- refresh 45 s, retry 12 s, movement trigger 250 m;
- maximum signal points 1400.

Any change to these values is a new feature/change request and is outside migration scope.

## V2 ownership

Owner: Dynamic Road Marks.

Traffic signals must have their own typed registry/snapshot. A signal update may replace the signal snapshot only. It must not clear convenience, fuel, facility or stop-sign state.

## V2 implementation split

### Acquisition
A narrow signal provider produces immutable signal coordinates.

For the first migration, preserve the proven acquisition behavior rather than simultaneously changing data source and renderer. External acquisition is therefore temporarily allowed for the frozen signal feature only. It is not precedent for static POIs.

A later native-MWM signal investigation may be performed separately. It cannot replace the accepted source unless real-device equivalence is proven.

### Direction classifier
Input:
- current valid device location;
- current valid bearing;
- signal coordinate.

Output:
- normal;
- forward-emphasized.

If bearing/location is unavailable, output normal. Geographic signal coordinates are never moved.

### Renderer
Use the smallest proven CoMaps-compatible mark extension needed to preserve the accepted rendering. Do not reuse a generic shared supplemental-point switch statement for unrelated feature families.

Required presentation mapping:
- z14 -> cb6-signal-xs
- z15 -> cb6-signal-s
- forward z17 -> cb6-signal-m
- forward z19 -> cb6-signal-l

### Resources
Signal SVGs are responsibility-owned V2 resources. Configure/generated atlas output must be audited after generation. Missing atlas symbols are a build failure.

## Historical lessons retained, implementations rejected

Retain these lessons:
- a symbol file existing in source does not prove it exists in the generated atlas;
- UserMark type/group is constructor-controlled in pinned CoMaps;
- overriding a non-virtual mark-type accessor is invalid;
- first-N Overpass ordering is not nearest-first;
- a heavy mixed signal/convenience request can suppress signals on mobile links;
- one feature publisher clearing a shared group can erase another feature.

Reject as V2 architecture:
- chronological application of v1.6/v1.8/v1.11/etc patch scripts;
- shared signal + convenience + stop response ownership;
- synthetic test signal in production;
- whole-group publisher shared by unrelated feature families;
- validator requirements tied to obsolete historical function names.

## Migration implementation gate

Before build:
1. start from successful Gate 0B source;
2. apply one consolidated V2 signal module/transform;
3. verify no convenience/fuel/facility implementation was introduced;
4. verify frozen constants/resources;
5. verify signal registry cannot clear unrelated feature state;
6. compile Python/Java/C++ touched surfaces where practical;
7. run generated-atlas audit after configure;
8. build arm64;
9. verify package/ABI/resources;
10. install/test on CB6 and compare with accepted Run #65 behavior.

## Acceptance

GitHub Actions success proves only build integrity.

Signal migration is complete only when CB6 real-device testing confirms:
- signal visibility around 500 m;
- accepted standard size around 200 m;
- no 1 km clutter;
- forward-only close enlargement;
- expected nearby coverage;
- no regression in base CoMaps behavior.

Until then status remains MIGRATION-IN-PROGRESS.
