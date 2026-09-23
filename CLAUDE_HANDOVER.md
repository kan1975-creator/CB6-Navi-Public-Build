# CB6 Navi — Claude Development Handover

## Immediate objective
Do not redesign the application. The first objective is to produce one installable arm64 APK for real-device testing on ATOTO CB6 (Android 13). Until an APK artifact exists, do not call the build complete. After APK generation it is only a real-device test build; final completion requires CB6 testing.

## Repositories / refs
- Public working repo: `kan1975-creator/CB6-Navi-Public-Build`
- Public working branch: `clean-import`
- Private source-of-truth repo: `kan1975-creator/CB6-Navi-Complete`
- Private source-of-truth branch: `cb6-runtime-final`
- Public state before this handover: `ae83cecea17761290636b3eba65d7080189b65e3`
- Workflow: `.github/workflows/build_cb6_voice_final.yml`
- applicationId target: `jp.cb6.navi`

Claude currently cannot access the private repository. Therefore treat the Public repo plus this document as the working handover. If files are missing, request the specific missing files rather than redesigning the app.

## Current CI state
Run #8 was triggered by commit `ae83cece` after restoring `scripts/apply_cb6_v13_display_fixes.py` from the Private source. At the latest check it was running and had completed checkout, package validation, Java setup and dependencies, and was cloning pinned CoMaps. Build/APK stages had not yet been reached.

Previous Run #7 passed the v1.2 patch after `apply_cb6_v12_fixes.py` was made tolerant of CoMaps source formatting changes, then failed because `apply_cb6_v13_display_fixes.py` was absent from Public. That v1.3 script has now been restored.

Important: do not repeat the former failure mode of discovering one missing file per CI run. Before another repair cycle, inventory every file referenced by the workflow and patch/audit chain and verify all are present together.

## Product constraints
- Base: CoMaps. Preserve standard CoMaps navigation functionality unless a change is explicitly required for CB6.
- Android target hardware: ATOTO CB6, Android 13, floating display use.
- No paid Google Maps Platform / Mapbox registration. Keep operation free where possible.
- Japanese UI.
- Do not silently remove or replace existing functionality.
- User wants minimal intervention: only ask when a genuine product decision/specification change is unavoidable.

## Confirmed CB6 requirements
- Traffic signals displayed with zoom-dependent sizing; overview small, closer zoom larger. Signal icons should be slim, with dark housing rendered as semi-transparent gray where implemented. Avoid excessive signals at ~1 km; normal display around driving zooms and emphasize relevant forward-direction signals when supported.
- Stop signs.
- Convenience stores with brand-specific marks: 7-Eleven, FamilyMart, Lawson, Seicomart, Ministop, Daily Yamazaki, My Basket. Convenience icons slightly larger than ordinary POIs.
- Gas stations always useful/visible by appropriate zoom policy.
- Major POIs: stations, hospitals, supermarkets, department stores, airports, roadside stations, parks, public facilities, parking etc. Large facilities should have more prominent labels.
- Reduce fine address/neighbourhood clutter except at close zoom.
- NAVITIME-like road readability: no unnecessary building emphasis, clear road colors/widths/text/scale.
- Search box persistent; search/history/favorites UI, including deletion.
- Voice search is required eventually, but do not delay the first installable APK solely to add new voice-search work.
- Google Maps launch button may be retained as an auxiliary action.
- Day/night switching.
- Heading-up / north-up toggle via compass.
- Vehicle position should be below screen center rather than centered.
- Current road-name HUD near bottom center, compact single line, ellipsize long names, avoid overlap with controls.
- Current-location button bottom-left, settings bottom-right, compass top-left, scale below compass. Google button should not overlap the road HUD/right controls.
- Scale default around 200 m, remembered; scale adjustment requirement 0.2 increments.
- Orientation mode: auto / portrait / landscape.
- No speed display requirement.
- Suppress stationary GPS jitter / false 0–2 km/h movement where possible.
- Startup should return to current location and restore intended map orientation/state after CB6 reboot.

## Known history / cautions
- Signals previously displayed in earlier builds; current work is a regression/recovery, not proof that the feature is impossible.
- There have been cases where signals disappeared near the vehicle or around ~100 m; preserve checks for zoom thresholds and atlas/symbol generation.
- POI icons have disappeared or overlapped in prior iterations. Symbol-atlas generation must be verified after resource generation.
- Current-location response, heading rotation lag, rotation pivot and compass accuracy have been prior issues.
- Search history/favorite deletion was previously missing.
- Do not change the original vehicle icon unless explicitly requested.
- A previous APK named `CB6-Navi-Ver1.0-Complete-arm64.apk` was successfully generated in an earlier Actions lineage, so this project is known to be APK-buildable. Do not restart architecture from scratch solely because the current Public migration is inconsistent.

## Recommended recovery procedure
1. Inspect `.github/workflows/build_cb6_voice_final.yml` and enumerate every repository-local file it directly invokes/copies.
2. Recursively inspect invoked patch/audit scripts for additional repository-local dependencies.
3. Verify the complete dependency set exists before triggering another run.
4. Preserve the pinned CoMaps revision used by the workflow unless a concrete incompatibility requires changing it.
5. Run patches in workflow order locally/CI and fix source-contract mismatches semantically rather than fragile byte-for-byte replacements when safe.
6. Run only the existing audits needed to protect the current specification; do not spend time inventing another audit framework.
7. Build the production arm64 APK.
8. Verify package/applicationId, ABI/native libraries, signing/installability basics and required generated resources/symbol atlas.
9. Upload APK as a GitHub Actions artifact.
10. Give the user the artifact for ATOTO CB6 real-device testing.

## Definition of next success
A GitHub Actions run reaches `Upload APK`, produces a downloadable arm64 APK artifact, and the artifact passes basic package/ABI/resource checks. This is the next milestone. Visual/behavioral defects are handled after the first real-device test instead of blocking APK delivery indefinitely.

## User communication
Do not say a build is progressing unless its actual CI status was checked. Do not give an ETA while CI is already failed. State only observed states: queued/running/failed + exact failing step/fixed + commit/rerun/APK generated. The user has already spent substantial time waiting for an APK, so prioritize tangible build output over planning prose.
