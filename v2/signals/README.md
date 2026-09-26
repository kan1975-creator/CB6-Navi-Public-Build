# Gate 1 — frozen traffic-signal migration

Owner: Dynamic Road Marks. Status: implementation / build verification pending; **not device-accepted**.

Upstream: CoMaps `7113ccb5f086183f8884b2aa4e58c987466b6704`.
Policy authority: `docs/CB6_V2_TRAFFIC_SIGNAL_MIGRATION.md`, accepted V1 Run #65.
Cross-project comparison: traffic-signal row already DESIGN-COMPLETE in `docs/CB6_V2_CROSS_PROJECT_COMPARISON.md`.

## Implementation and impact

- `SignalProvider` / `OverpassSignalProvider`: isolated real OSM traffic-signal nodes, existing three endpoints, 3 km query, 4/8-second connection/read timeouts. No static POI acquisition.
- `SignalSnapshot`: immutable signal records, nearest-first sorting before dedup/cap of 1400.
- `SignalPolicy`: frozen 45-second refresh, 12-second retry, 250-metre movement, forward 450 metres / ±45 degrees.
- `SignalCache`: versioned signal-only cache, previous 24-hour retention, independent from map FeatureIDs. Cache/network failures retain the last valid snapshot.
- `SignalController`: main-thread lifecycle/render publication; single-flight worker for acquisition/cache. Generation tokens reject late results after stop/recreation. New fixes without bearing revert to normal size rather than reusing an old bearing. Refresh timers also work while stationary. Logs are DEBUG-only.
- `cb6_signal_mark.hpp`: proven DebugMarkPoint direct-symbol rendering; z14 XS, z15 small, only forward z17 medium/z19 large. In pinned `user_mark_shapes.cpp`, `SymbolIsPOI=false` enters direct symbol batching rather than ordinary POI collision. Do not restore the legacy POI/depth overrides.
- `cb6_signal_jni.inc`: matched arrays, finite-coordinate validation before mutation, dedicated `CB6_SIGNAL` type, clear/show/create/notify all use that type. Invalid input retains the previous scene.
- `apply_signals.py`: one anchored, idempotent transform. No historical patch execution, no post-configure reapplication.

The typed DebugMarkPoint constructor only changes the underlying group for the new signal subclass. Stock DebugMarkPoint keeps its original constructor and renderer defaults. `BookmarkManager` initializes all registered enum groups generically, so no bookmark implementation edit is needed.

Changed upstream surfaces: identity build.gradle; six additive MwmActivity hooks; SDK Java declaration/JNI include; UserMark enum/typed constructor/debug name; new responsibility-owned Java/header/JNI files and eight SVGs. Standard map styles (including native close-zoom signal styling), search, routing, location, bookmarks and other POIs remain stock. No convenience, fuel, facility, stop, camera, voice or HUD feature is ported here.

The S/M/L source SVG bytes come from the existing repository icons. XS is the exact SVG authored by the accepted half-size transform. No unrelated icon is copied. No foreign-project source code is imported; the previously documented external comparisons inform ownership only.

## Validation

Gate 1 workflow compiles every Python source (including dormant historical references), runs executable Java boundary/dense-response tests, applies the module twice, checks all changed surfaces and generated-source hashes, runs configure, verifies source hashes again, and checks all 12 day/night density atlases before Gradle.

APK validation checks CRC, application id/label, signing, arm64-only native libraries, AArch64 ELF, the exact JNI entrypoint and all four signal names in the native library and every packaged atlas. SHA256, source identity, module sources, diff and logs travel with the artifact. Failure evidence is uploaded separately.

Real-device acceptance remains open: compare 500m/200m/1km visibility, forward-only enlargement, nearby physical signal coverage, restart/theme changes and stock CoMaps behavior against Run #65. CI cannot prove physical-device rendering or live mobile-network coverage.
