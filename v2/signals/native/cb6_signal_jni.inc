// Included inside Framework.cpp's existing extern "C" section.
// Caller: Android main thread, matching BookmarkManager's thread contract.
JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6Signals(
    JNIEnv * env, jclass, jdouble originLat, jdouble originLon, jlongArray idArray, jdoubleArray latArray, jdoubleArray lonArray, jbooleanArray forwardArray, jdoubleArray memberLatArray, jdoubleArray memberLonArray, jdoubleArray centerLatArray, jdoubleArray centerLonArray, jlongArray memberIdArray, jlongArray centerIdArray)
{
  if (!idArray || !latArray || !lonArray || !forwardArray || !memberLatArray || !memberLonArray || !centerLatArray || !centerLonArray || !memberIdArray || !centerIdArray)
  {
    LOG(LINFO, ("CB6-SIGNAL-DIAG", "jni-reject-null"));
    return;
  }
  jsize const n = env->GetArrayLength(latArray);
  LOG(LINFO, ("CB6-SIGNAL-DIAG", "jni-enter", n));
  if (n > 1400 || env->GetArrayLength(idArray) != n || env->GetArrayLength(lonArray) != n || env->GetArrayLength(forwardArray) != n) return;
  jsize const topologyN = env->GetArrayLength(memberLatArray);
  if (topologyN > 1400 || env->GetArrayLength(memberLonArray) != topologyN || env->GetArrayLength(centerLatArray) != topologyN || env->GetArrayLength(centerLonArray) != topologyN || env->GetArrayLength(memberIdArray) != topologyN || env->GetArrayLength(centerIdArray) != topologyN) return;
  std::vector<jdouble> memberLats(topologyN), memberLons(topologyN), centerLats(topologyN), centerLons(topologyN);
  std::vector<jlong> memberIds(topologyN), centerIds(topologyN);
  if (topologyN > 0)
  {
    env->GetDoubleArrayRegion(memberLatArray, 0, topologyN, memberLats.data()); if (env->ExceptionCheck()) return;
    env->GetDoubleArrayRegion(memberLonArray, 0, topologyN, memberLons.data()); if (env->ExceptionCheck()) return;
    env->GetDoubleArrayRegion(centerLatArray, 0, topologyN, centerLats.data()); if (env->ExceptionCheck()) return;
    env->GetDoubleArrayRegion(centerLonArray, 0, topologyN, centerLons.data()); if (env->ExceptionCheck()) return;
    env->GetLongArrayRegion(memberIdArray, 0, topologyN, memberIds.data()); if (env->ExceptionCheck()) return;
    env->GetLongArrayRegion(centerIdArray, 0, topologyN, centerIds.data()); if (env->ExceptionCheck()) return;
  }
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

  // Group identity is the topology-verified centre ID, never centre proximity.
  // If the same ID refers to inconsistent centre coordinates, it is untrusted.
  auto const reliableGroupId = [&](jlong groupId)
  {
    if (groupId <= 0) return false;
    jsize first = -1;
    for (jsize t = 0; t < topologyN; ++t)
    {
      if (centerIds[t] != groupId) continue;
      if (first < 0) { first = t; continue; }
      if (distanceMeters(centerLats[t], centerLons[t], centerLats[first], centerLons[first]) > kDirectDuplicateM)
        return false;
    }
    return first >= 0;
  };

  std::vector<ms::LatLon> normalizedMwmSignals;
  std::vector<jlong> normalizedMwmGroupIds;
  for (auto const & mwm : mwmSignals)
  {
    jlong mappedGroup = 0;
    jsize memberIndex = -1;
    bool ambiguous = false;
    for (jsize t = 0; t < topologyN; ++t)
    {
      if (distanceMeters(mwm.m_lat, mwm.m_lon, memberLats[t], memberLons[t]) > kDirectDuplicateM) continue;
      if (memberIds[t] <= 0 || !reliableGroupId(centerIds[t]))
      {
        ambiguous = true;
        break;
      }
      if (mappedGroup != 0 && mappedGroup != centerIds[t])
      {
        ambiguous = true;
        break;
      }
      mappedGroup = centerIds[t];
      memberIndex = t;
    }
    if (!ambiguous && memberIndex >= 0)
    {
      // Do not conflate two different groups, even if their centres are adjacent.
      bool alreadyMapped = false;
      for (auto const & existingId : normalizedMwmGroupIds)
        if (existingId == mappedGroup) { alreadyMapped = true; break; }
      if (!alreadyMapped)
      {
        normalizedMwmSignals.emplace_back(centerLats[memberIndex], centerLons[memberIndex]);
        normalizedMwmGroupIds.push_back(mappedGroup);
      }
    }
    else
    {
      // Missing, colliding or ambiguous topology: preserve the raw MWM signal.
      normalizedMwmSignals.push_back(mwm);
      normalizedMwmGroupIds.push_back(0);
    }
  }

  auto const groupForMark = [&](jlong pointId, double lat, double lon, jlong mwmGroupId) -> jlong
  {
    if (mwmGroupId > 0) return reliableGroupId(mwmGroupId) ? mwmGroupId : 0;
    jlong matchedGroup = 0;
    for (jsize t = 0; t < topologyN; ++t)
    {
      bool const memberMatch = pointId > 0 && memberIds[t] == pointId
          && distanceMeters(lat, lon, memberLats[t], memberLons[t]) <= kDirectDuplicateM;
      bool const centerMatch = pointId > 0 && centerIds[t] == pointId
          && distanceMeters(lat, lon, centerLats[t], centerLons[t]) <= kDirectDuplicateM;
      if (!memberMatch && !centerMatch) continue;
      if (!reliableGroupId(centerIds[t])) return 0;
      if (matchedGroup != 0 && matchedGroup != centerIds[t]) return 0;
      matchedGroup = centerIds[t];
    }
    return matchedGroup;
  };

  // Only 200m visibility is thinned. Every mark is still created at z17+.
  std::vector<jlong> shown200mGroupIds;
  auto const keepAt200m = [&](jlong pointId, double lat, double lon, jlong mwmGroupId)
  {
    jlong const groupId = groupForMark(pointId, lat, lon, mwmGroupId);
    if (groupId == 0) return true; // Fail open: never hide unknown/colliding marks.
    for (auto const & shownId : shown200mGroupIds)
      if (shownId == groupId) return false;
    shown200mGroupIds.push_back(groupId);
    return true;
  };

  auto session = frm()->GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CB6_SIGNAL);
  session.SetIsVisible(UserMark::Type::CB6_SIGNAL, true);
  size_t created = 0, suppressed = 0, mwmCreated = 0;
  for (size_t mwmIndex = 0; mwmIndex < normalizedMwmSignals.size(); ++mwmIndex)
  {
    auto const & mwm = normalizedMwmSignals[mwmIndex];
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(mwm.m_lat, mwm.m_lon));
    mark->SetForward(false);
    mark->SetShowAt200m(keepAt200m(0, mwm.m_lat, mwm.m_lon, normalizedMwmGroupIds[mwmIndex]));
    ++created;
    ++mwmCreated;
  }
  constexpr jlong kWayIdNamespace = (static_cast<jlong>(1) << 62);
  for (jsize i = 0; i < n; ++i)
  {
    bool directDuplicate = false;
    if (ids[i] > 0 && ids[i] < kWayIdNamespace)
    {
      for (auto const & mwm : normalizedMwmSignals)
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
    mark->SetShowAt200m(keepAt200m(ids[i], lats[i], lons[i], 0));
    ++created;
  }
  LOG(LINFO, ("CB6-SIGNAL-MWM-DUP-DIAG", "suppression-complete", "mwm-raw", mwmSignals.size(), "mwm-created", mwmCreated, "suppressed", suppressed));
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
