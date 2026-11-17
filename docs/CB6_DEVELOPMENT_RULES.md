# CB6 Navi development rules

## Purpose
Prevent repeat regressions and unnecessary GitHub Actions runs. A feature is not complete merely because it compiles or displays once.

## Fixed constraints
- Preserve previously confirmed PASS results; do not rerun them without a change that invalidates the evidence.
- Do not alter signal feature E1005, the six convenience-store brand assets, or approved symbol sizes unless the task explicitly requires it.
- Keep offline MWM as the convenience POI source. Do not silently add online dependencies.
- Use the pinned repository branch and CoMaps commit; verify current HEAD before a non-force update.
- Do not launch additional Actions runs or retry a failed run without authorization.

## Mandatory pre-implementation review (only changed code and directly affected paths)
1. Identify the user-visible success criterion and relevant historical failures (especially map pan freezes, missing marks, duplicate intersection signals).
2. Trace the full execution path across Java, JNI, C++, rendering and lifecycle callbacks. Check declaration order and Java compile-time references.
3. Identify work performed on Android's UI thread. Never treat a delay/debounce as proof that heavy work is safe.
4. For MWM reads, establish the native thread-safety contract before moving work to a worker thread. Plan cancellation/stale-result suppression, bounded queries and cache invalidation.
5. Confirm gesture and zoom behavior, refresh triggers, screen visibility, and behavior on pause/resume.
6. Define the minimum static checks and the specific runtime checks needed. Do not claim performance or compilation success without evidence.
7. Consolidate related fixes into one scoped change where possible. Avoid speculative fixes and unrelated cleanup.

## Convenience-mark performance acceptance
- Panning and zooming remain responsive; no reproducible UI stall attributable to convenience POI collection.
- No unnecessary repeated full-range MWM query on every gesture.
- Latest viewport wins: obsolete results cannot overwrite a newer viewport.
- Work is bounded by viewport/cache strategy, with explicit limits; do not assume a fixed 3 km radius is optimal.
- Preserve the six brand marks, sizes, native UserMark rendering, and offline behavior.
- Check on device at the approved scales, including pan, zoom and pause/resume.

## Build and evidence discipline
- Before a new run, review the exact diff for Java compile risks, JNI signatures, thread use, lifecycle and resource paths.
- Prefer local/static validation where available; do not rerun unrelated previously passing stages.
- One authorized new Actions run per candidate. Record commit SHA, run ID, first failing step, and APK artifact name/size.
- Diagnostic artifact is not an installable APK unless APK contents are verified.
- Distinguish: source reviewed / compiled / built / installed / device verified. Never conflate these states.
- On failure, inspect the first concrete error, make the smallest justified correction, and request a new authorized run.
- No extra governance-only steps that delay APK delivery.

## Review checklist
- [ ] Previous relevant defects reviewed and addressed or explicitly marked as outstanding
- [ ] UI-thread workload and native thread safety evaluated
- [ ] Java/JNI/C++ interfaces and lifecycle reviewed
- [ ] Offline behavior, brand assets, sizes and E1005 preserved
- [ ] Changed code checked without rerunning unrelated PASS stages
- [ ] Acceptance criteria and remaining risks reported accurately
- [ ] HEAD and authorized Actions run scope verified
