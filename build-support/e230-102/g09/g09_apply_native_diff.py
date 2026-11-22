#!/usr/bin/env python3
"""G09 SQLite-only differential reconciliation; run after native snapshot scripts."""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit('usage: g09_apply_native_diff.py <comaps-root>')
root=Path(sys.argv[1]); cpp=root/'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp'; java=root/'android/sdk/src/main/java/app/organicmaps/sdk/Framework.java'; activity=root/'android/app/src/main/java/app/organicmaps/MwmActivity.java'
if not all(x.is_file() for x in (cpp,java,activity)): raise SystemExit('STOP: required generated sources missing')
c=cpp.read_text(); j=java.read_text(); a=activity.read_text()
start='JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6ConvenienceMarks(\n    JNIEnv * env, jclass, jdoubleArray latsArray, jdoubleArray lonsArray, jintArray kindsArray)\n{'
if c.count(start)!=1: raise SystemExit('STOP: original JNI signature mismatch')
function_end=c.find('\n}\n',c.index(start))
if function_end<0: raise SystemExit('STOP: JNI function terminator missing')
block=c[c.index(start):function_end+3]
if 'static std::map<ShopKey, kml::MarkId> shopMarks;' not in block or 'session.DeleteUserMark(item.second);' not in block: raise SystemExit('STOP: existing map/reset not confirmed')
if block.count('    session.SetIsVisible(UserMark::Type::CONVENIENCE, true);')!=2: raise SystemExit('STOP: expected reset + add branches missing')
block=block.replace(start,'static void Cb6ApplyConvenienceMarks(\n    JNIEnv * env, jdoubleArray latsArray, jdoubleArray lonsArray, jintArray kindsArray, bool snapshot)\n{',1)
# For snapshots, collect desired keys. MWM append-only path does not prune.
needle='  if (n > 0)\n  {\n    auto session = currentManager->GetEditSession();\n    size_t added = 0, kept = 0;'
repl='  if (n > 0)\n  {\n    auto session = currentManager->GetEditSession();\n    std::set<ShopKey> desired;\n    size_t added = 0, kept = 0;'
if block.count(needle)!=1: raise SystemExit('STOP: positive marks branch mismatch')
block=block.replace(needle,repl,1)
needle='      ShopKey const key{lats[i], lons[i], static_cast<int>(kinds[i])};\n'
if block.count(needle)!=1: raise SystemExit('STOP: key declaration mismatch')
block=block.replace(needle,needle+'      if (snapshot) desired.insert(key);\n',1)
needle='    session.SetIsVisible(UserMark::Type::CONVENIENCE, true);\n    LOG(LINFO, ("CB6-CONVENIENCE-DIAG append-only"'
if block.count(needle)!=1: raise SystemExit('STOP: positive visibility anchor mismatch')
repl='''    if (snapshot)
    {
      for (auto it = shopMarks.begin(); it != shopMarks.end(); )
      {
        if (desired.find(it->first) == desired.end())
        {
          session.DeleteUserMark(it->second);
          it = shopMarks.erase(it);
        }
        else
          ++it;
      }
    }
    session.SetIsVisible(UserMark::Type::CONVENIENCE, true);
    LOG(LINFO, ("CB6-CONVENIENCE-DIAG append-only"'''
block=block.replace(needle,repl,1)
# Empty SQLite snapshots use the existing convenience-only reset; no MWM behavior changes.
wrappers='''
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6ConvenienceMarks(
    JNIEnv * env, jclass, jdoubleArray lats, jdoubleArray lons, jintArray kinds)
{
  Cb6ApplyConvenienceMarks(env, lats, lons, kinds, false);
}

JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSyncCb6ConvenienceMarks(
    JNIEnv * env, jclass, jdoubleArray lats, jdoubleArray lons, jintArray kinds)
{
  Cb6ApplyConvenienceMarks(env, lats, lons, kinds, true);
}
'''
old=c[c.index(start):function_end+3]
c=c.replace(old,block+wrappers,1)
include='#include <set>\n'
if include not in c:
  anchor='#include "app/organicmaps/sdk/Framework.hpp"\n'
  if c.count(anchor)!=1: raise SystemExit('STOP: C++ include anchor mismatch')
  c=c.replace(anchor,anchor+include,1)
old='  public static native void nativeSetCb6ConvenienceMarks(double[] lats, double[] lons, int[] kinds);'
if j.count(old)!=1: raise SystemExit('STOP: Java JNI declaration mismatch')
j=j.replace(old,old+'\n  public static native void nativeSyncCb6ConvenienceMarks(double[] lats, double[] lons, int[] kinds);',1)
old='              Framework.nativeSetCb6ConvenienceMarks(marks.lats, marks.lons, marks.kinds);'
if a.count(old)!=1: raise SystemExit('STOP: SQLite snapshot calls mismatch')
a=a.replace(old,'              Framework.nativeSyncCb6ConvenienceMarks(marks.lats, marks.lons, marks.kinds);',1)
# The legacy explanatory comment must not falsely say a reset occurs each frame.
a=a.replace('              // The G09 reset extension clears only dedicated convenience marks.\n              // Both calls run on the UI thread with generation/paused guards.', '              // Reconcile only dedicated convenience marks in one native edit session.\n              // The call runs on the UI thread with generation/paused guards.')
# Fail-closed: all checks above complete before writes.
for p,s in ((cpp,c),(java,j),(activity,a)):p.write_text(s)
print('G09_NATIVE_DIFF_APPLIED: 3 generated files, SQLite-only sync; MWM original JNI retained')
