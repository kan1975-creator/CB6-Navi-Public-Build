// Included inside Framework.cpp's existing extern "C" section.
// Caller: Android main thread, matching BookmarkManager's thread contract.
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6Signals(
    JNIEnv * env, jclass, jdouble originLat, jdouble originLon, jlongArray idArray, jdoubleArray latArray, jdoubleArray lonArray, jbooleanArray forwardArray)
{
  if (!idArray || !latArray || !lonArray || !forwardArray)
  {
    LOG(LINFO, ("CB6-SIGNAL-DIAG", "jni-reject-null"));
    return;
  }
  jsize const n = env->GetArrayLength(latArray);
  LOG(LINFO, ("CB6-SIGNAL-DIAG", "jni-enter", n));
  if (n > 1400 || env->GetArrayLength(idArray) != n || env->GetArrayLength(lonArray) != n || env->GetArrayLength(forwardArray) != n) return;
  std::vector<jlong> ids(n);
  std::vector<jdouble> lats(n), lons(n);
  std::vector<jboolean> forward(n);
  if (n > 0)
  {
    env->GetLongArrayRegion(idArray, 0, n, ids.data());
    if (env->ExceptionCheck()) return;
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

  if (!std::isfinite(originLat) || !std::isfinite(originLon) || originLat < -90.0 || originLat > 90.0
      || originLon < -180.0 || originLon > 180.0) return;
  std::vector<ms::LatLon> mwmSignals;
  auto const center = mercator::FromLatLon(originLat, originLon);
  auto const rect = mercator::RectByCenterXYAndSizeInMeters(center, 3000.0);
  static uint32_t const signalType = classif().GetTypeByPath({"highway", "traffic_signals"});
  frm()->GetDataSource().ForEachInRect([&](FeatureType & ft)
  {
    if (ft.GetGeomType() != feature::GeomType::Point) return;
    feature::TypesHolder types(ft);
    if (!types.Has(signalType)) return;
    mwmSignals.push_back(mercator::ToLatLon(ft.GetCenter()));
  }, rect, scales::GetUpperScale());

  constexpr double kDirectDuplicateM = 0.5;
  constexpr double kEarthRadiusM = 6371000.0;
  constexpr double kPi = 3.14159265358979323846;
  auto const distanceMeters = [&](double lat1, double lon1, double lat2, double lon2)
  {
    double const p1 = lat1 * kPi / 180.0, p2 = lat2 * kPi / 180.0;
    double const dp = (lat2 - lat1) * kPi / 180.0, dl = (lon2 - lon1) * kPi / 180.0;
    double const a = std::sin(dp / 2.0) * std::sin(dp / 2.0)
        + std::cos(p1) * std::cos(p2) * std::sin(dl / 2.0) * std::sin(dl / 2.0);
    return 2.0 * kEarthRadiusM * std::asin(std::sqrt(a));
  };

  auto session = frm()->GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CB6_SIGNAL);
  session.SetIsVisible(UserMark::Type::CB6_SIGNAL, true);
  size_t created = 0, suppressed = 0, mwmCreated = 0;\n  for (auto const & mwm : mwmSignals)\n  {\n    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(mwm.m_lat, mwm.m_lon));\n    mark->SetForward(false);\n    ++created;\n    ++mwmCreated;\n  }\n  constexpr jlong kWayIdNamespace = (static_cast<jlong>(1) << 62);
  for (jsize i = 0; i < n; ++i)
  {
    bool directDuplicate = false;
    if (ids[i] > 0 && ids[i] < kWayIdNamespace)
    {
      for (auto const & mwm : mwmSignals)
      {
        if (distanceMeters(mwm.m_lat, mwm.m_lon, lats[i], lons[i]) <= kDirectDuplicateM)
        {
          directDuplicate = true;
          break;
        }
      }
    }
    if (directDuplicate)
    {
      ++suppressed;
      LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "direct-duplicate-suppressed", "overpass-node", ids[i]));
      continue;
    }
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(lats[i], lons[i]));
    mark->SetForward(forward[i] == JNI_TRUE);
    ++created;
  }
  LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "suppression-complete", "mwm-created", mwmCreated, "suppressed", suppressed));
  LOG(LINFO, ("CB6-SIGNAL-DIAG", "marks-created", created));
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
    LOG(LINFO, ("CB6-SIGNAL-MWM-DIAG", "point", count, "latE7", std::llround(ll.m_lat * 10000000.0),
        "lonE7", std::llround(ll.m_lon * 10000000.0)));
  }, rect, scales::GetUpperScale());
  LOG(LINFO, ("CB6-SIGNAL-MWM-DIAG", "complete", count, lat, lon));
}


// Read-only diagnostic: compare raw Overpass signal-node coordinates with stock MWM
// traffic-signal features in the existing 1000 m diagnostic search area.
// Does not create, remove, filter, or alter any map mark.
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeLogCb6MwmDirectDuplicateCandidates(
    JNIEnv * env, jclass, jdouble lat, jdouble lon, jlongArray idArray,
    jdoubleArray latArray, jdoubleArray lonArray)
{
  LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "enter"));
  if (!std::isfinite(lat) || !std::isfinite(lon) || lat < -90.0 || lat > 90.0 || lon < -180.0 || lon > 180.0) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "invalid-origin")); return; }
  if (!idArray || !latArray || !lonArray) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "null-array")); return; }
  jsize const n = env->GetArrayLength(idArray);
  if (n > 1400) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "node-count-over-1400", "node-count", n)); return; }
  if (env->GetArrayLength(latArray) != n || env->GetArrayLength(lonArray) != n) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "array-length-mismatch", "node-count", n)); return; }
  std::vector<jlong> ids(n);
  std::vector<jdouble> lats(n), lons(n);
  if (n > 0)
  {
    env->GetLongArrayRegion(idArray, 0, n, ids.data());
    if (env->ExceptionCheck()) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "id-array-exception")); return; }
    env->GetDoubleArrayRegion(latArray, 0, n, lats.data());
    if (env->ExceptionCheck()) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "lat-array-exception")); return; }
    env->GetDoubleArrayRegion(lonArray, 0, n, lons.data());
    if (env->ExceptionCheck()) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "lon-array-exception")); return; }
  }
  for (jsize i = 0; i < n; ++i)
    if (ids[i] <= 0 || !std::isfinite(lats[i]) || !std::isfinite(lons[i]) || lats[i] < -90.0 || lats[i] > 90.0 || lons[i] < -180.0 || lons[i] > 180.0) { LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "early-return", "reason", "invalid-node", "index", i)); return; }
  LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "validated", "node-count", n));

  auto const center = mercator::FromLatLon(lat, lon);
  auto const rect = mercator::RectByCenterXYAndSizeInMeters(center, 1000.0);
  static uint32_t const signalType = classif().GetTypeByPath({"highway", "traffic_signals"});
  size_t candidateCount = 0;
  constexpr double kEarthRadiusM = 6371000.0;
  constexpr double kPi = 3.14159265358979323846;
  auto const distanceMeters = [&](double lat1, double lon1, double lat2, double lon2)
  {
    double const p1 = lat1 * kPi / 180.0;
    double const p2 = lat2 * kPi / 180.0;
    double const dp = (lat2 - lat1) * kPi / 180.0;
    double const dl = (lon2 - lon1) * kPi / 180.0;
    double const a = std::sin(dp / 2.0) * std::sin(dp / 2.0)
        + std::cos(p1) * std::cos(p2) * std::sin(dl / 2.0) * std::sin(dl / 2.0);
    return 2.0 * kEarthRadiusM * std::asin(std::sqrt(a));
  };

  frm()->GetDataSource().ForEachInRect([&](FeatureType & ft)
  {
    if (ft.GetGeomType() != feature::GeomType::Point)
      return;
    feature::TypesHolder types(ft);
    if (!types.Has(signalType))
      return;
    auto const mwmLl = mercator::ToLatLon(ft.GetCenter());
    for (jsize i = 0; i < n; ++i)
    {
      double const distance = distanceMeters(mwmLl.m_lat, mwmLl.m_lon, lats[i], lons[i]);
      if (distance > 0.5)
        continue;
      ++candidateCount;
      LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "direct-duplicate-candidate",
          "mwm-latE7", std::llround(mwmLl.m_lat * 10000000.0),
          "mwm-lonE7", std::llround(mwmLl.m_lon * 10000000.0),
          "overpass-node", ids[i],
          "overpass-latE7", std::llround(lats[i] * 10000000.0),
          "overpass-lonE7", std::llround(lons[i] * 10000000.0),
          "distance-m", distance));
    }
  }, rect, scales::GetUpperScale());
  LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "complete", "candidate-count", candidateCount));
}
