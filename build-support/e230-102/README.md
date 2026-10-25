# CB6 E-2-30-16-102 — staged Work handoff

Dedicated branch only. No Actions run is authorized by registration. Main and pre-existing workflows remain unchanged.

The 57 binary parts concatenate in numeric order to the unmodified CB6_E230_166_RECOVERY_APK_UNGENERATED.zip. manifest.json pins each part and the complete archive. apply_handoff.py checks that identity, applies SOURCE_FROM_FIXED_COMAPS.patch to CoMaps 7113ccb5f086183f8884b2aa4e58c987466b6704, verifies SOURCE_SHA256.json, and copies generated_overlay. It does not reimplement signal logic, run old feature tests, generate a map database, or execute the archive's old runner scripts.

The release build variant deliberately uses the upstream public CoMaps debug keystore, preserving jp.cb6.navi and avoiding the debug variant's ASAN runtime. Production signing inputs are rejected. No Release publishing is implemented. Native compilation will occur as part of a future APK build on the fresh Actions runner; the historic native PASS and 53 test PASS are inherited evidence, not new execution claims.

Gradle 8.14.4, Java 21, SDK 36, NDK 28.2.13676358, CMake 3.22.1, and protobuf 3.20.3 are selected. Gradle downloads missing dependencies using the fixed source's existing repositories and versions. The dependency preflight is not an APK build. assembleWebRelease appears once, with no retry. First-run and first-attempt guards deny subsequent dispatches/reruns; even a failed first run consumes that workflow's permitted run. APK existence, signature fingerprint, arm64 library and required assets are checked only after successful build. Always-upload preserves available failure logs too. Real-device acceptance remains pending.

## Activation limits

Only workflow_dispatch is declared. The approved_commit input must match the dedicated branch's exact dispatch SHA and the actor must be kan1975-creator. GitHub normally requires a workflow_dispatch file to exist on the default branch before dispatch. This task does NOT modify main: this workflow may therefore remain undispatchable until a separate owner-approved activation arrangement is made. Repository Actions policy, action permissions, network dependencies and runner capacity also apply. Registration is not evidence of a successful APK build.

## Limited publication review

356 nested archive entries inspected for private keys, credential tokens, signed URLs and sensitive filenames; none detected. The fixed debug signing password matches the pinned public upstream build.gradle. No production signing keystore or secure.properties file is bundled. Original logs include workspace paths, version metadata and historic test results. This is a limited review, not an assurance against every possible secret format.
