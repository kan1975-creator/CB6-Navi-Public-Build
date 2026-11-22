#!/usr/bin/env python3
"""Apply verified pinned CoMaps viewport JNI additions, isolated/fail-closed."""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit('usage: apply_g09_viewport_native.py <comaps-root>')
root=Path(sys.argv[1])
files={
 'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.hpp': (
  '  m2::PointD GetViewportCenter() const;',
  '  m2::PointD GetViewportCenter() const;\n  m2::RectD GetCb6ViewportBounds() const;'),
 'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp': (
  'm2::PointD Framework::GetViewportCenter() const\n{\n  return m_work.GetViewportCenter();\n}',
  'm2::PointD Framework::GetViewportCenter() const\n{\n  return m_work.GetViewportCenter();\n}\n\nm2::RectD Framework::GetCb6ViewportBounds() const\n{\n  return m_work.GetCurrentViewport();\n}'),
 'android/sdk/src/main/java/app/organicmaps/sdk/Framework.java': (
  '  public static native double[] nativeGetScreenRectCenter();',
  '  public static native double[] nativeGetScreenRectCenter();\n\n  /** [minLat, maxLat, minLon, maxLon], current projected map viewport. */\n  public static native double[] nativeGetCb6ViewportBounds();'),
}
cpp='android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp'
needle='JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeShowTrackRect'
insert="""JNIEXPORT jdoubleArray JNICALL Java_app_organicmaps_sdk_Framework_nativeGetCb6ViewportBounds(JNIEnv * env, jclass)
{
  auto const rect = frm()->GetCb6ViewportBounds();
  double const bounds[] = {
      mercator::YToLat(rect.minY()), mercator::YToLat(rect.maxY()),
      mercator::XToLon(rect.minX()), mercator::XToLon(rect.maxX())};
  jdoubleArray result = env->NewDoubleArray(4);
  if (result != nullptr)
    env->SetDoubleArrayRegion(result, 0, 4, bounds);
  return result;
}

"""
# Stage changes in memory and write only after every anchor matches.
changes={}
for path,(old,new) in files.items():
 f=root/path
 if not f.is_file(): raise SystemExit('STOP: missing '+path)
 txt=f.read_text()
 if txt.count(old)!=1 or new in txt: raise SystemExit('STOP: anchor mismatch '+path)
 changes[f]=txt.replace(old,new,1)
f=root/cpp
if changes[f].count(needle)!=1 or 'nativeGetCb6ViewportBounds(JNIEnv' in changes[f]:
 raise SystemExit('STOP: JNI anchor mismatch')
changes[f]=changes[f].replace(needle,insert+needle,1)
for f,txt in changes.items(): f.write_text(txt)
print('G09_VIEWPORT_NATIVE_APPLIED: 3 files; no signal/POI/MWM edits')
