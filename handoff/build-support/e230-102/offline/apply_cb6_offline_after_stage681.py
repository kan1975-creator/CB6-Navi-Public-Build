#!/usr/bin/env python3
"""Apply offline-only signal acquisition after stage681. Fail on changed anchors."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("usage: apply_cb6_offline_after_stage681.py COMAPS_ROOT")
root = Path(sys.argv[1]).resolve()
java = root / "android/app/src/main/java/app/organicmaps/cb6/signals/SignalController.java"
jni = root / "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc"
if not java.is_file() or not jni.is_file():
    raise SystemExit("STOP: missing overlaid source")
j, n = java.read_text(), jni.read_text()
def one(source, before, after, label):
    count = source.count(before)
    if count != 1:
        raise SystemExit(f"STOP: {label}: expected one anchor, got {count}")
    return source.replace(before, after, 1)
j = one(j,
    "this.provider = new CompositeSignalProvider(\n        new CompositeSignalProvider(new OverpassSignalProvider(), new VerifiedSignalProvider()),\n        new SQLiteSignalProvider(this.context));",
    "this.provider = new SQLiteSignalProvider(this.context);", "offline provider")
n = one(n, "#include <unordered_map>",
    "#include <unordered_map>\n#include <unordered_set>", "header")
n = one(n, "std::vector<jlong> createdGroupIds;",
    "std::unordered_set<jlong> createdGroupIds;", "group set")
n = one(n,
    "    for (auto const & createdId : createdGroupIds)\n      if (createdId == groupId) return false;\n    createdGroupIds.push_back(groupId);\n    return true;",
    "    return createdGroupIds.insert(groupId).second;", "group insertion")
java.write_text(j)
jni.write_text(n)
print("CB6 offline-only source patch applied; compilation not yet verified")
