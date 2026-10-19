// Included inside Framework.cpp's existing extern "C" section.
// Additional read-only viewport JNI; existing nativeSetCb6Signals 12 args unchanged.
JNIEXPORT jdoubleArray JNICALL Java_app_organicmaps_sdk_Framework_nativeGetCb6SignalViewportBounds(
    JNIEnv * env, jclass)
{
  m2::RectD const view = frm()->GetCurrentViewport();
  auto const sw = mercator::ToLatLon(m2::PointD(view.minX(), view.minY()));
  auto const ne = mercator::ToLatLon(m2::PointD(view.maxX(), view.maxY()));
  jdouble bounds[4] = {sw.m_lat, sw.m_lon, ne.m_lat, ne.m_lon};
  if (!std::isfinite(bounds[0]) || !std::isfinite(bounds[1]) ||
      !std::isfinite(bounds[2]) || !std::isfinite(bounds[3])) return nullptr;
  jdoubleArray out = env->NewDoubleArray(4);
  if (out != nullptr) env->SetDoubleArrayRegion(out, 0, 4, bounds);
  return out;
}

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
  if (n > 50000 || env->GetArrayLength(idArray) != n || env->GetArrayLength(lonArray) != n || env->GetArrayLength(forwardArray) != n) return;
  jsize const topologyN = env->GetArrayLength(memberLatArray);
  if (topologyN > 50000 || env->GetArrayLength(memberLonArray) != topologyN || env->GetArrayLength(centerLatArray) != topologyN || env->GetArrayLength(centerLonArray) != topologyN || env->GetArrayLength(memberIdArray) != topologyN || env->GetArrayLength(centerIdArray) != topologyN) return;
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

  // R35 FAIL-3: index topology identities once instead of 50k-by-50k scans.
  // No new upstream includes: this fragment uses only existing std::vector/cmath.
  constexpr size_t kCb6BucketCount = 131071;
  auto const idBucket = [&](jlong id) -> size_t
  {
    unsigned long long x = static_cast<unsigned long long>(id);
    x ^= x >> 33;
    x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33;
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return static_cast<size_t>(x % kCb6BucketCount);
  };
  // 1e-5 degree cells. Nearby queries examine all cells that can fall within 0.5m.
  auto const cellId = [](jlong y, jlong x) -> jlong
  {
    return (y + 9000000LL) * 36000001LL + (x + 18000000LL) + 1LL;
  };
  auto const cellFor = [&](double lat, double lon) -> jlong
  {
    return cellId(static_cast<jlong>(std::floor(lat * 100000.0)),
                  static_cast<jlong>(std::floor(lon * 100000.0)));
  };
  struct Cb6GroupInfo
  {
    jlong id;
    jsize first;
    bool trusted;
  };
  std::vector<Cb6GroupInfo> cb6Groups;
  std::vector<std::vector<size_t>> cb6GroupIndex(kCb6BucketCount);
  std::vector<std::vector<jsize>> cb6MemberIdIndex(kCb6BucketCount);
  std::vector<std::vector<jsize>> cb6MemberCells(kCb6BucketCount);
  for (jsize t = 0; t < topologyN; ++t)
  {
    if (memberIds[t] > 0) cb6MemberIdIndex[idBucket(memberIds[t])].push_back(t);
    if (std::isfinite(memberLats[t]) && std::isfinite(memberLons[t]) &&
        memberLats[t] >= -90 && memberLats[t] <= 90 &&
        memberLons[t] >= -180 && memberLons[t] <= 180)
      cb6MemberCells[idBucket(cellFor(memberLats[t], memberLons[t]))].push_back(t);
    if (centerIds[t] <= 0) continue;
    auto & groupBucket = cb6GroupIndex[idBucket(centerIds[t])];
    size_t group = cb6Groups.size();
    for (auto const idx : groupBucket)
      if (cb6Groups[idx].id == centerIds[t]) { group = idx; break; }
    if (group == cb6Groups.size())
    {
      cb6Groups.push_back({centerIds[t], t,
          std::isfinite(centerLats[t]) && std::isfinite(centerLons[t]) &&
          centerLats[t] >= -90 && centerLats[t] <= 90 &&
          centerLons[t] >= -180 && centerLons[t] <= 180});
      groupBucket.push_back(group);
    }
    else
    {
      auto & stored = cb6Groups[group];
      if (!std::isfinite(centerLats[t]) || !std::isfinite(centerLons[t]) ||
          !stored.trusted ||
          distanceMeters(centerLats[t], centerLons[t],
                         centerLats[stored.first], centerLons[stored.first]) > kDirectDuplicateM)
        stored.trusted = false;
    }
  }
  auto const getGroup = [&](jlong groupId) -> Cb6GroupInfo const *
  {
    if (groupId <= 0) return nullptr;
    for (auto const idx : cb6GroupIndex[idBucket(groupId)])
      if (cb6Groups[idx].id == groupId) return &cb6Groups[idx];
    return nullptr;
  };
  auto const reliableGroupId = [&](jlong groupId)
  {
    auto const * group = getGroup(groupId);
    return group != nullptr && group->trusted;
  };

  // At high latitudes inspect every candidate instead of risking a grid miss.
  // Hash collisions only cost extra exact 0.5m comparisons; they never cause hiding.
  auto const nearby = [&](double lat, double lon,
                          std::vector<std::vector<jsize>> const & cells,
                          jsize count, auto const & visit)
  {
    if (!std::isfinite(lat) || !std::isfinite(lon)) return;
    constexpr double kPiCb6 = 3.14159265358979323846;
    double const cosLat = std::cos(lat * kPiCb6 / 180.0);
    if (cosLat < 0.01)
    {
      for (jsize i = 0; i < count; ++i) if (visit(i)) return;
      return;
    }
    double const lonCells = (kDirectDuplicateM / (111195.0 * cosLat)) * 100000.0;
    if (lonCells > 31.0)
    {
      for (jsize i = 0; i < count; ++i) if (visit(i)) return;
      return;
    }
    int const xRadius = static_cast<int>(std::ceil(lonCells)) + 1;
    jlong const cy = static_cast<jlong>(std::floor(lat * 100000.0));
    jlong const cx = static_cast<jlong>(std::floor(lon * 100000.0));
    for (jlong y = cy - 1; y <= cy + 1; ++y)
      for (jlong x = cx - xRadius; x <= cx + xRadius; ++x)
        for (jsize const idx : cells[idBucket(cellId(y, x))])
          if (visit(idx)) return;
  };

  // Keep all original MWM anchors; proximity alone never certifies an intersection.
  std::vector<jlong> mwmGroupIds(mwmSignals.size(), 0);
  for (size_t mwmIndex = 0; mwmIndex < mwmSignals.size(); ++mwmIndex)
  {
    auto const & mwm = mwmSignals[mwmIndex];
    jlong mappedGroup = 0;
    bool ambiguous = false;
    nearby(mwm.m_lat, mwm.m_lon, cb6MemberCells, topologyN, [&](jsize t)
    {
      if (distanceMeters(mwm.m_lat, mwm.m_lon, memberLats[t], memberLons[t]) > kDirectDuplicateM)
        return false;
      if (memberIds[t] <= 0 || !reliableGroupId(centerIds[t]))
      {
        ambiguous = true;
        return true;
      }
      if (mappedGroup != 0 && mappedGroup != centerIds[t])
      {
        ambiguous = true;
        return true;
      }
      mappedGroup = centerIds[t];
      return false;
    });
    if (!ambiguous && mappedGroup > 0) mwmGroupIds[mwmIndex] = mappedGroup;
  }
  // Direct MWM duplicate queries are also spatially indexed (no point-by-all-MWM scan).
  std::vector<std::vector<jsize>> cb6MwmCells(kCb6BucketCount);
  for (jsize m = 0; m < static_cast<jsize>(mwmSignals.size()); ++m)
  {
    auto const & mwm = mwmSignals[m];
    if (std::isfinite(mwm.m_lat) && std::isfinite(mwm.m_lon) &&
        mwm.m_lat >= -90 && mwm.m_lat <= 90 && mwm.m_lon >= -180 && mwm.m_lon <= 180)
      cb6MwmCells[idBucket(cellFor(mwm.m_lat, mwm.m_lon))].push_back(m);
  }

  auto const groupForMark = [&](jlong pointId, double lat, double lon, jlong mwmGroupId) -> jlong
  {
    if (mwmGroupId > 0) return reliableGroupId(mwmGroupId) ? mwmGroupId : 0;
    if (pointId <= 0) return 0;
    jlong matchedGroup = 0;
    for (jsize t : cb6MemberIdIndex[idBucket(pointId)])
    {
      if (!(memberIds[t] == pointId) ||
          distanceMeters(lat, lon, memberLats[t], memberLons[t]) > kDirectDuplicateM) continue;
      if (!reliableGroupId(centerIds[t])) return 0;
      if (matchedGroup != 0 && matchedGroup != centerIds[t]) return 0;
      matchedGroup = centerIds[t];
    }
    for (size_t idx : cb6GroupIndex[idBucket(pointId)])
    {
      auto const & group = cb6Groups[idx];
      if (!(group.id == pointId) ||
          distanceMeters(lat, lon, centerLats[group.first], centerLons[group.first]) > kDirectDuplicateM)
        continue;
      if (!group.trusted) return 0;
      if (matchedGroup != 0 && matchedGroup != group.id) return 0;
      matchedGroup = group.id;
    }
    return matchedGroup;
  };

  std::vector<jlong> shown200mGroupIds;
  std::vector<std::vector<jlong>> shown200mIndex(kCb6BucketCount);
  auto const keepAt200m = [&](jlong pointId, double lat, double lon, jlong mwmGroupId)
  {
    jlong const groupId = groupForMark(pointId, lat, lon, mwmGroupId);
    if (groupId == 0) return true; // Fail open: never hide unknown/colliding marks.
    for (auto const & shownId : shown200mIndex[idBucket(groupId)])
      if (shownId == groupId) return false;
    shown200mGroupIds.push_back(groupId);
    shown200mIndex[idBucket(groupId)].push_back(groupId);
    return true;
  };

  auto session = frm()->GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CB6_SIGNAL);
  session.SetIsVisible(UserMark::Type::CB6_SIGNAL, true);
  size_t created = 0, suppressed = 0, mwmCreated = 0;
  for (size_t mwmIndex = 0; mwmIndex < mwmSignals.size(); ++mwmIndex)
  {
    auto const & mwm = mwmSignals[mwmIndex];
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(mwm.m_lat, mwm.m_lon));
    mark->SetForward(false);
    mark->SetShowAt200m(keepAt200m(0, mwm.m_lat, mwm.m_lon, mwmGroupIds[mwmIndex]));
    ++created;
    ++mwmCreated;
  }
  constexpr jlong kWayIdNamespace = (static_cast<jlong>(1) << 62);
  for (jsize i = 0; i < n; ++i)
  {
    bool directDuplicate = false;
    if (ids[i] > 0 && ids[i] < kWayIdNamespace)
    {
      nearby(lats[i], lons[i], cb6MwmCells, static_cast<jsize>(mwmSignals.size()), [&](jsize m)
      {
        auto const & mwm = mwmSignals[m];
        if (distanceMeters(mwm.m_lat, mwm.m_lon, lats[i], lons[i]) <= kDirectDuplicateM)
        {
          directDuplicate = true;
          return true;
        }
        return false;
      });
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
