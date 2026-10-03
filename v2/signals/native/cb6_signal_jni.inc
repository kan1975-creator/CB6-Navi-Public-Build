// Included inside Framework.cpp's existing extern "C" section.
// Caller: Android main thread, matching BookmarkManager's thread contract.
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6Signals(
    JNIEnv * env, jclass, jdoubleArray latArray, jdoubleArray lonArray, jbooleanArray forwardArray)
{
  if (!latArray || !lonArray || !forwardArray)
  {
    LOG(LINFO, ("CB6-SIGNAL-DIAG", "jni-reject-null"));
    return;
  }
  jsize const n = env->GetArrayLength(latArray);
  LOG(LINFO, ("CB6-SIGNAL-DIAG", "jni-enter", n));
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
  LOG(LINFO, ("CB6-SIGNAL-DIAG", "marks-created", n));
  session.NotifyChanges();
  LOG(LINFO, ("CB6-SIGNAL-DIAG", "notify-complete", n));
}


// Read-only diagnostic: enumerate stock MWM traffic-signal features near the supplied location.
// Does not create, remove, or alter any map mark.
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeLogCb6MwmSignals(
    JNIEnv *, jclass, jdouble lat, jdouble lon)
{
  if (!std::isfinite(lat) || !std::isfinite(lon) || lat < -90.0 || lat > 90.0 || lon < -180.0 || lon > 180.0)
    return;
  auto const center = mercator::FromLatLon(lat, lon);
  auto const rect = mercator::RectByCenterXYAndSizeInMeters(center, 1000.0);
  static uint32_t const signalType = classif().GetTypeByPath({"highway", "traffic_signals"});
  size_t count = 0;
  frm()->GetDataSource().ForEachInRect([&](FeatureType & ft)
  {
    if (ft.GetGeomType() != feature::GeomType::Point)
      return;
    feature::TypesHolder types(ft);
    if (!types.Has(signalType))
      return;
    auto const pt = ft.GetCenter();
    auto const ll = mercator::ToLatLon(pt);
    ++count;
    LOG(LINFO, ("CB6-SIGNAL-MWM-DIAG", "point", count, "latE7", std::llround(ll.m_lat * 10000000.0),\n        "lonE7", std::llround(ll.m_lon * 10000000.0)));
  }, rect, scales::GetUpperScale());
  LOG(LINFO, ("CB6-SIGNAL-MWM-DIAG", "complete", count, lat, lon));
}
