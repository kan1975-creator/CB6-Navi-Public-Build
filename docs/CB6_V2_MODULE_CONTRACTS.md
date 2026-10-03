# CB6 V2 Module Contracts

Status: RETIRED AS CANONICAL — PRIOR DESIGN INPUT PENDING REVALIDATION\n\nDuring `OVERALL_DESIGN_REBUILD`, this file is evidence only. It must not authorize implementation or override the active Requirement Registry / rebuilt overall design.
Baseline: `comaps/comaps@7113ccb5f086183f8884b2aa4e58c987466b6704`

This file converts the overall design into enforceable module contracts. V2 implementation must not bypass these boundaries.

## Baseline / build

Owns:
- pinned upstream provenance;
- reproducible configure/build;
- CB6 package/identity changes once introduced;
- arm64 APK verification.

May depend on: upstream build system.
Must not own: feature behavior.

## Native POI Access

Owns:
- read-only nearby MWM feature iteration;
- FeatureID/center/type/name/brand/operator extraction;
- category filtering;
- deterministic distance/cap handling.

Input: center, radius, category mask, limit.
Output: immutable native POI records.

May depend on: Framework/FeaturesFetcher/DataSource/FeatureType/classificator.
Must not depend on:
- Android UI;
- network/Overpass;
- UserMark groups;
- search history;
- routing;
- bookmarks.

## POI Classifier

Owns:
- category normalization;
- brand/operator/name normalization;
- canonical brand enum;
- evidence-source priority and generic fallback.

Input: native POI evidence.
Output: normalized POI identity.

May depend on: small normalization utilities.
Must not depend on renderer, Android lifecycle, network or routing.

## POI Presentation

Owns:
- category/brand icon choice;
- zoom-size policy;
- category-specific label policy;
- static POI collision/priority integration.

Input: normalized native POI identity + zoom.
Must not acquire POIs from network.
Must not clear Dynamic Road Marks.

## Dynamic Road Marks

Owns:
- traffic signals;
- future directional stop marks;
- typed feature-specific update registries;
- atomic rendering snapshots.

Must preserve frozen signal behavior.
Must not own convenience/fuel/facility static MWM POIs.
No publisher may clear another feature type as a side effect.

## Location / Camera

Owns:
- follow mode;
- north lock;
- own-position screen offset;
- heading/camera transition policy;
- stopped/low-speed presentation stability.

Input: stock location/heading/routing state.
Must not mutate geographic GPS coordinates.

## Road HUD

Owns current-road presentation only.
Consumes existing routing/address state.
Must not create an online geocoder or navigation state.

## Search / Voice

Owns:
- text/voice input normalization;
- Japanese aliases;
- speech lifecycle/fallback.

Output always feeds stock CoMaps SearchEngine.
Must not maintain a parallel search index/database.

## Routing Policy

Owns CB6-specific route-option semantics such as free-expressway-only.
Must operate inside native route calculation semantics.
Must not post-filter a completed route in Android UI.

## Toll Information

Owns fee data association and display model after authoritative data source is proven.
Must not infer exact fee from road class or fabricate a price.

## Favorites Sync

Owns only the later synchronization adapter.
BookmarkManager remains authoritative.
Must use item/category identity and conflict metadata.
Must not scrape labels or destructively replace the whole collection.

## UI / Settings

Owns:
- visual controls/layout;
- CB6 preference persistence;
- user commands into modules.

Must not directly mutate renderer internals, DataSource, routing graph or BookmarkManager storage.

## Diagnostics

Owns development-only evidence collection.
Must be build-flag guarded or removable.
Must not fabricate production POIs or change normal map behavior.

## Dependency direction

Allowed high-level direction:

`UI -> module API -> native core`

`Native POI Access -> POI Classifier -> POI Presentation`

`stock location -> Location/Camera -> UI/renderer presentation`

`voice/text -> Search/Voice -> stock SearchEngine`

Forbidden:
- renderer -> Android UI state;
- classifier -> renderer;
- POI access -> network;
- static POI presentation -> signal publisher;
- UI -> raw DataSource mutation;
- feature module -> unrelated feature state.

## Cross-module update rule

Data passed between V2 modules is an immutable typed snapshot or a narrow command. Shared mutable lists are prohibited for unrelated feature families.

## Implementation review gate

Before adding a source file or API:
1. assign exactly one owning module;
2. list upstream dependencies;
3. prove it does not introduce a forbidden dependency;
4. update this contract if a legitimate new dependency is discovered;
5. then implement.

A build that compiles while violating these contracts is a failed V2 architecture build.
