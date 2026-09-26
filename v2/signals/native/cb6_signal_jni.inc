// Included inside Framework.cpp's existing extern "C" section.
// Caller: Android main thread, matching BookmarkManager's thread contract.
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6Signals(
    JNIEnv * env, jclass, jdoubleArray latArray, jdoubleArray lonArray, jbooleanArray forwardArray)
{
  if (!latArray || !lonArray || !forwardArray) return;
  jsize const n = env->GetArrayLength(latArray);
  if (n > 1400 || env->GetArrayLength(lonArray) != n || env->GetArrayLength(forwardArray) != n) return;
  std::vector<jdouble> lats(n), lons(n);
  std::vector<jboolean> forward(n);
  if (n > 0)
  {
    env->GetDoubleArrayRegion(latArray, 0, n, lats.data());
    if (env->ExceptionCheck()) return;
    env->GetDoubleArrayRegion(lonArray, 0, n, lons.data());
    if (env->ExceptionCheck()) return;
    env->GetBooleanArrayRegion(forwardArray, 0, n, forward.data());
    if (env->ExceptionCheck()) return;
  }
  // Reject malformed snapshots before touching the last valid renderer state.
  for (jsize i = 0; i < n; ++i)
    if (!std::isfinite(lats[i]) || !std::isfinite(lons[i]) || lats[i] < -90.0 || lats[i] > 90.0
        || lons[i] < -180.0 || lons[i] > 180.0) return;

  auto session = frm()->GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CB6_SIGNAL);
  session.SetIsVisible(UserMark::Type::CB6_SIGNAL, true);
  for (jsize i = 0; i < n; ++i)
  {
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(lats[i], lons[i]));
    mark->SetForward(forward[i] == JNI_TRUE);
  }
  session.NotifyChanges();
}
