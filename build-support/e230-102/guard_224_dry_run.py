#!/usr/bin/env python3
"""Fail-closed Gradle dry-run gate. This checks task graph text, not actual side effects."""
import pathlib,re,sys
if len(sys.argv)!=2: raise SystemExit('STOP: expected dry-run log path')
s=pathlib.Path(sys.argv[1]).read_text(errors='replace')
task_lines=re.findall(r'^(?:> Task )?(:[^\s]+)(.*)$',s,re.M)
if not task_lines or any('SKIPPED' not in tail for _,tail in task_lines):
    raise SystemExit('STOP: not a recognized all-SKIPPED dry-run task graph')
tasks=[task for task,_ in task_lines]
if not tasks: raise SystemExit('STOP: no Gradle tasks recognized in dry-run output')
required={':app:processWebReleaseResources',':app:compileWebReleaseJavaWithJavac'}
if not required.issubset(set(tasks)): raise SystemExit('STOP: required compile/resource tasks absent')
# Fail closed for any packaging/signing/assembly/bundling or install/publish tasks, including indirect dependencies.
blocked=re.compile(r'(assemble|package|sign|validateSigning|bundle|apk|install|publish|upload|deploy|zipalign|aab|extractApks|create.*Artifact)',re.I)
allowed_intermediate_tasks={
    ':sdk:packageReleaseResources',
    ':app:packageWebReleaseResources',
    ':app:processWebReleaseManifestForPackage',
    ':sdk:bundleLibCompileToJarRelease',
}
violations=[t for t in tasks if t not in allowed_intermediate_tasks and blocked.search(t.split(':')[-1])]
if violations: raise SystemExit('STOP: forbidden Gradle tasks: '+', '.join(violations))
print('PASS: dry-run graph has required tasks and no known APK/signing/packaging tasks')
