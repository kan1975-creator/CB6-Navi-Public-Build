## CB6 Navi change review

Read [CB6 development rules](../docs/CB6_DEVELOPMENT_RULES.md) before approval.

- [ ] Scope and known past failures reviewed (especially pan/zoom freeze)
- [ ] UI thread, JNI/native thread safety, query bounds and stale-result handling checked
- [ ] Java/JNI/C++ connections and lifecycle checked
- [ ] Existing E1005, offline-only operation, six brand assets and symbol sizes preserved
- [ ] Existing PASS results reused; no unrelated reruns
- [ ] Exact changed-code checks and device acceptance criteria recorded
- [ ] New Actions run is separately authorized; commit and HEAD verified

### Evidence and outstanding risks
Describe which claims are source-reviewed, compiled, built or device-verified. List unresolved risks explicitly.
