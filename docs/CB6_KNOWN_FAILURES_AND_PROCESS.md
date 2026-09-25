# CB6 Known Failures and Mandatory Development Process

This file exists so the development method does not regress after a time gap or new session.

## Mandatory process — applies to every current and future CB6 task

1. Do not fix only the failing line.
2. Identify the changed concept/name/flow.
3. Search the entire repository for old references and old assumptions.
4. Inspect implementation scripts, generated-source templates, audits, workflow grep/invariants, resources and regression checks.
5. Inspect workflow ordering for later scripts that can restore stale behavior.
6. Update all affected implementation and validation locations together.
7. Check frozen/completed features for unintended changes.
8. Check known historical failure patterns and Python/Java/C++ syntax before build.
9. Inspect final generated source, not only patch source.
10. Build only after the full preflight.
11. On failure, repeat the root-cause sweep.
12. Never change correct implementation merely to satisfy a stale validator; update the validator when it no longer represents the specification.
13. GitHub Actions success is not completion. APK verification + CB6 real-device behavior is final authority.
14. Minimize build count through analysis/preflight.

## Known failure classes

### Stale renamed-flow validators
Historical example: `buildPoiQuery` was replaced by split convenience/stop acquisition, but old scripts/audits still required the obsolete name. Multiple builds were wasted by finding these one at a time.

Prevention: repository-wide obsolete-symbol search before build; audits should verify required behavior, not arbitrary implementation names.

### Literal escaped newline contamination
Python patch generation has produced literal `\\n` in Java/C++/validator output.

Prevention: parse Python scripts before build; inspect generated Java/C++ anchors; do not assume a Python string rendered as intended.

### Later patch restores old state
Sequential `apply_cb6_*` scripts and configure/resource generation can overwrite earlier changes.

Prevention: treat workflow order as architecture; inspect final generated tree after all final patches.

### UserMark group mismatch
A class derived from `DebugMarkPoint` may default to `DEBUG_MARK`. If JNI clears/shows `CB6_DRIVING`, the mark can be created into a different group and never appear as intended.

Prevention: audit constructor mark type + ClearGroup + SetIsVisible + CreateUserMark + NotifyChanges together.

### Whole-group replacement erases unrelated marks
`nativeSetCb6DrivingMarks` rebuilds the CB6 mark group. A signal-only update can erase stores/stops.

Prevention: merge retained non-signal marks before publish; dedicated schedulers must share a coherent retained dataset.

### Build success mistaken for feature success
Run #87/#91 examples: valid arm64 APK does not mean convenience icons are visible.

Prevention: acceptance state remains NOT FROZEN until user verifies on CB6.

### Network dependency where MWM already contains data
Stock CoMaps can already show many POIs from downloaded MWM. Duplicating them via Overpass adds failure modes.

Prevention: before network supplementation, inspect native MWM/classificator/style path and prefer it when it can satisfy the spec.

## Debugging hierarchy

For a missing map feature, check in this order:
1. Is feature present in MWM/search/place data?
2. Is correct internal classificator type/brand available?
3. Does active default/vehicle style include it at this zoom?
4. Does symbol exist in generated atlas?
5. Is overlay blocked by priority/collision? Use `?debug-rect` where useful.
6. For UserMarks: did data reach Java parser?
7. Did retained dataset contain it?
8. Did JNI receive it?
9. Correct UserMark type/group?
10. Correct symbol name and zoom?
11. Did a later update clear the group?

This ordering prevents repeatedly rebuilding the renderer when acquisition is actually zero, and vice versa.

## Documentation maintenance rule

When architecture knowledge changes, update:
- `CB6_COMAPS_ARCHITECTURE.md`
- `CB6_CHANGE_IMPACT_MAP.md`
- `CB6_FROZEN_FEATURES.md`
- this file
in the same change where practical.
