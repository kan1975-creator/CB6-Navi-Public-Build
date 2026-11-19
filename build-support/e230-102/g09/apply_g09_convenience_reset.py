
from pathlib import Path
import sys
root=Path(sys.argv[1])
fw=root/'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp'
act=root/'android/app/src/main/java/app/organicmaps/MwmActivity.java'
s=fw.read_text()
anchor='  if (n > 0)\n  {\n    auto session = currentManager->GetEditSession();'
addition='''  // Empty arrays are a reset of dedicated CB6 convenience marks only.
  if (n == 0)
  {
    auto session = currentManager->GetEditSession();
    for (auto const & item : shopMarks)
      session.DeleteUserMark(item.second);
    shopMarks.clear();
    session.SetIsVisible(UserMark::Type::CONVENIENCE, true);
    env->ReleaseDoubleArrayElements(latsArray, lats, JNI_ABORT);
    env->ReleaseDoubleArrayElements(lonsArray, lons, JNI_ABORT);
    env->ReleaseIntArrayElements(kindsArray, kinds, JNI_ABORT);
    return;
  }
'''
if s.count(anchor)!=1: raise SystemExit('STOP: JNI anchor mismatch')
a=act.read_text()
old='    app.organicmaps.sdk.MapView.setCb6OnGestureEnd(mCb6ConvenienceGestureEnd);'
new='''    Framework.nativeSetCb6ConvenienceMarks(new double[0], new double[0], new int[0]);
    mCb6ConvenienceCovered.clear();
    app.organicmaps.sdk.MapView.setCb6OnGestureEnd(mCb6ConvenienceGestureEnd);'''
if a.count(old)!=1: raise SystemExit('STOP: lifecycle anchor mismatch')
fw.write_text(s.replace(anchor,addition+anchor,1))
act.write_text(a.replace(old,new,1))
print('G09 convenience-only reset patch applied')
