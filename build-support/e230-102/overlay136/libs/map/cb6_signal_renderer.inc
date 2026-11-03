// E230: approved E229 merge and grouping logic, invoked for the rendered viewport.
void Framework::SetCb6Signals(Cb6SignalSnapshot snapshot)
{
  m_cb6Signals = std::move(snapshot);
  UpdateCb6Signals(m_currentModelView);
}

void Framework::UpdateCb6Signals(ScreenBase const & screen)
{
  auto const mode = df::Cb6Mode(df::GetDrawTileScale(screen), gui::RulerHelper::GetMetricRulerMeters(screen));
  auto session = GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CB6_SIGNAL);
  session.SetIsVisible(UserMark::Type::CB6_SIGNAL, mode != df::Cb6SignalMode::Hidden);
  if (mode == df::Cb6SignalMode::Hidden) { session.NotifyChanges(); return; }
  auto const & ids = m_cb6Signals.ids;
  auto const & lats = m_cb6Signals.lats;
  auto const & lons = m_cb6Signals.lons;
  auto const & forward = m_cb6Signals.forward;
  auto const & memberLats = m_cb6Signals.memberLats;
  auto const & memberLons = m_cb6Signals.memberLons;
  auto const & centerLats = m_cb6Signals.centerLats;
  auto const & centerLons = m_cb6Signals.centerLons;
  auto const & memberIds = m_cb6Signals.memberIds;
  auto const & centerIds = m_cb6Signals.centerIds;
  int const n = static_cast<int>(lats.size());
  int const topologyN = static_cast<int>(memberLats.size());
  std::vector<ms::LatLon> mwmSignals;
  auto const rect = screen.ClipRect();
  static uint32_t const signalType = classif().GetTypeByPath({"highway", "traffic_signals"});
  GetDataSource().ForEachInRect([&](FeatureType & ft)
  {
    if (ft.GetGeomType() != feature::GeomType::Point) return;
    // MWM interval queries may return points in neighboring index cells.
    if (!rect.IsPointInside(ft.GetCenter())) return;
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
  auto const reliableGroupId = [&](int64_t groupId)
  {
    if (groupId <= 0) return false;
    int first = -1;
    for (int t = 0; t < topologyN; ++t)
    {
      if (centerIds[t] != groupId) continue;
      if (first < 0) { first = t; continue; }
      if (distanceMeters(centerLats[t], centerLons[t], centerLats[first], centerLons[first]) > kDirectDuplicateM)
        return false;
    }
    if (first < 0) return false;
    // Root identity must be backed by a signal record, not an arbitrary group ID.
    bool rootPresent = false;
    for (int i = 0; i < n; ++i)
      if (ids[i] == groupId && distanceMeters(lats[i], lons[i],
            centerLats[first], centerLons[first]) <= kDirectDuplicateM)
        rootPresent = true;
    if (!rootPresent) return false;
    // Direct/non-transitive: every member must be <=15m from this same root.
    for (int t = 0; t < topologyN; ++t)
      if (centerIds[t] == groupId &&
          distanceMeters(memberLats[t], memberLons[t],
                         centerLats[first], centerLons[first]) > 15.0)
        return false;
    return true;
  };

  // Keep all original MWM signal anchors at every z17+ scale.
  // Topology only controls the display-only 200 m flag.
  std::vector<int64_t> mwmGroupIds(mwmSignals.size(), 0);
  for (size_t mwmIndex = 0; mwmIndex < mwmSignals.size(); ++mwmIndex)
  {
    auto const & mwm = mwmSignals[mwmIndex];
    int64_t mappedGroup = 0;
    bool ambiguous = false;
    for (int t = 0; t < topologyN; ++t)
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
    }
    if (!ambiguous && mappedGroup > 0) mwmGroupIds[mwmIndex] = mappedGroup;
  }

  auto const groupForMark = [&](int64_t pointId, double lat, double lon, int64_t mwmGroupId) -> int64_t
  {
    if (mwmGroupId > 0) return reliableGroupId(mwmGroupId) ? mwmGroupId : 0;
    int64_t matchedGroup = 0;
    for (int t = 0; t < topologyN; ++t)
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
  std::vector<int64_t> shown200mGroupIds;
  auto const keepAt200m = [&](int64_t pointId, double lat, double lon, int64_t mwmGroupId)
  {
    int64_t const groupId = groupForMark(pointId, lat, lon, mwmGroupId);
    if (groupId == 0) return true; // Fail open: never hide unknown/colliding marks.
    for (auto const & shownId : shown200mGroupIds)
      if (shownId == groupId) return false;
    shown200mGroupIds.push_back(groupId);
    return true;
  };

  size_t created = 0, suppressed = 0, mwmCreated = 0;
  for (size_t mwmIndex = 0; mwmIndex < mwmSignals.size(); ++mwmIndex)
  {
    auto const & mwm = mwmSignals[mwmIndex];
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(mwm.m_lat, mwm.m_lon));
    mark->SetFullScale(mode == df::Cb6SignalMode::All);
    mark->SetForward(false);
    mark->SetShowAt200m(keepAt200m(0, mwm.m_lat, mwm.m_lon, mwmGroupIds[mwmIndex]));
    ++created;
    ++mwmCreated;
  }
  for (int i = 0; i < n; ++i)
  {
    // Off-screen supplemental points must not consume a visible group representative.
    if (!rect.IsPointInside(mercator::FromLatLon(lats[i], lons[i]))) continue;
    bool directDuplicate = false;
    // Apply MWM-first coordinate dedup to both OSM nodes and ways.
    for (auto const & mwm : mwmSignals)
    {
      if (distanceMeters(mwm.m_lat, mwm.m_lon, lats[i], lons[i]) <= kDirectDuplicateM)
      {
        directDuplicate = true;
        break;
      }
    }
    if (directDuplicate)
    {
      ++suppressed;
      continue;
    }
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(lats[i], lons[i]));
    mark->SetFullScale(mode == df::Cb6SignalMode::All);
    mark->SetForward(forward[i] == 1);
    mark->SetShowAt200m(keepAt200m(ids[i], lats[i], lons[i], 0));
    ++created;
  }
  session.NotifyChanges();
}
