#!/usr/bin/env python3
"""Fail-closed Gradle dry-run gate. This checks task graph text, not actual side effects."""
import pathlib,re,sys
if len(sys.argv)!=2: raise SystemExit('STOP: expected dry-run log path')
s=pathlib.Path(sys.argv[1]).read_text(errors='replace')
# Recognize only complete Gradle task lines in both supported output formats.
task_pattern=re.compile(r'^(?:> Task )?(:[A-Za-z0-9_.-]+(?::[A-Za-z0-9_.-]+)*)(?:[ \t]+(.*))?$',re.M)
task_lines=[(m.group(1), (m.group(2) or '').strip()) for m in task_pattern.finditer(s)]
# A malformed task-like line must never silently disappear from the graph.
task_like=[line for line in s.splitlines() if re.match(r'^(?:> Task\b|:[A-Za-z0-9_.-])',line)]
if not task_lines or len(task_like)!=len(task_lines):
    raise SystemExit('STOP: missing or unrecognized Gradle task lines')
if any(tail!='SKIPPED' for _,tail in task_lines):
    raise SystemExit('STOP: Gradle task not exactly SKIPPED')
if len({task for task,_ in task_lines})!=len(task_lines):
    raise SystemExit('STOP: duplicate Gradle task')
if len(re.findall(r'^BUILD SUCCESSFUL in .+$',s,re.M))!=1 or re.search(r'^BUILD FAILED\b',s,re.M):
    raise SystemExit('STOP: missing or conflicting Gradle success marker')
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
