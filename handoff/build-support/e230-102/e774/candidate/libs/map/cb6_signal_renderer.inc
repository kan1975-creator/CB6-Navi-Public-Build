// E764: shared cache generation invalidation on new CB6 snapshot.
namespace
{
uint64_t & Cb6SignalSnapshotGeneration()
{
  static uint64_t generation = 0;
  return generation;
}
}
// E230: approved E229 merge and grouping logic, invoked for the rendered viewport.
void Framework::SetCb6Signals(Cb6SignalSnapshot snapshot)
{
  ++Cb6SignalSnapshotGeneration();
  m_cb6Signals = std::move(snapshot);
  UpdateCb6Signals(m_currentModelView);
}

void Framework::UpdateCb6Signals(ScreenBase const & screen)
{
  auto const mode = df::Cb6Mode(df::GetDrawTileScale(screen), gui::RulerHelper::GetMetricRulerMeters(screen));
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
  // E764: cache MWM coordinates across small viewport moves. All access remains
  // on the existing Framework viewport thread; no FeatureType escapes callback.
  auto const rect = screen.ClipRect();
  auto const dx = rect.maxX() - rect.minX();
  auto const dy = rect.maxY() - rect.minY();
  auto const queryRect = m2::RectD(rect.minX() - dx * 0.5, rect.minY() - dy * 0.5,
                                   rect.maxX() + dx * 0.5, rect.maxY() + dy * 0.5);
  struct MwmViewportCache
  {
    m2::RectD coverage;
    std::vector<ms::LatLon> signals;
    bool valid = false;
  };
  static Framework const * cachedOwner = nullptr;
  static MwmViewportCache cache;
  static uint64_t cachedGeneration = ~uint64_t{0};
  // The marks are generated for the full cached coverage, not only the screen.
  // Therefore a pan inside the coverage needs neither MWM I/O nor mark edits.
  static bool marksValid = false;
  static df::Cb6SignalMode renderedMode = df::Cb6SignalMode::Hidden;
  // Never reuse viewport marks or MWM coordinates across Framework instances.
  if (cachedOwner != this)
  {
    cache.valid = false;
    marksValid = false;
    cachedGeneration = ~uint64_t{0};
    cachedOwner = this;
  }
  if (cachedGeneration != Cb6SignalSnapshotGeneration())
  {
    cache.valid = false;
    marksValid = false;
    cachedGeneration = Cb6SignalSnapshotGeneration();
  }
  // Coverage containment is checked against the *current* screen, not its centre.
  bool const cacheHit = cache.valid && cache.coverage.IsPointInside(m2::PointD(rect.minX(), rect.minY()))
      && cache.coverage.IsPointInside(m2::PointD(rect.maxX(), rect.maxY()));
  // Hidden marks are independent of viewport coverage. Do not clear and notify
  // on every pan when the mode remains hidden.
  if (marksValid && renderedMode == mode &&
      (mode == df::Cb6SignalMode::Hidden || cacheHit))
    return;
  // Hidden mode must not query MWM. Keep bookmark edits on the original thread.
  if (mode == df::Cb6SignalMode::Hidden)
  {
    auto session = GetBookmarkManager().GetEditSession();
    session.ClearGroup(UserMark::Type::CB6_SIGNAL);
    session.SetIsVisible(UserMark::Type::CB6_SIGNAL, false);
    session.NotifyChanges();
    marksValid = true;
    renderedMode = mode;
    return;
  }
  // Query first; preserve existing visible marks if data loading fails.
  if (!cacheHit)
  {
    std::vector<ms::LatLon> fetched;
    static uint32_t const signalType = classif().GetTypeByPath({"highway", "traffic_signals"});
    GetDataSource().ForEachInRect([&](FeatureType & ft)
    {
      if (ft.GetGeomType() != feature::GeomType::Point) return;
      if (!queryRect.IsPointInside(ft.GetCenter())) return;
      feature::TypesHolder types(ft);
      if (!types.Has(signalType)) return;
      fetched.push_back(mercator::ToLatLon(ft.GetCenter()));
    }, queryRect, scales::GetUpperScale());
    cache.signals = std::move(fetched);
    cache.coverage = queryRect;
    cache.valid = true;
  }
  // Include the complete coverage in marks; Drape culls off-screen marks.
  // This is essential: otherwise an early return would hide signals after panning.
  std::vector<ms::LatLon> const & mwmSignals = cache.signals;
  // Only now mutate the marks, after the MWM query has completed.
  auto session = GetBookmarkManager().GetEditSession();
  session.ClearGroup(UserMark::Type::CB6_SIGNAL);
  session.SetIsVisible(UserMark::Type::CB6_SIGNAL, true);

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

  // E772: one representative mark per verified physical intersection at ALL
  // visible zoom levels. Unverified/non-intersection signals stay independent.
  // Prefer the MWM anchor when both MWM and supplemental records map to a group.
  std::vector<int64_t> representedGroups;
  auto const claimRepresentative = [&](int64_t groupId)
  {
    if (groupId <= 0) return true;
    if (std::find(representedGroups.begin(), representedGroups.end(), groupId) != representedGroups.end()) return false;
    representedGroups.push_back(groupId);
    return true;
  };

  size_t created = 0, suppressed = 0, mwmCreated = 0;
  for (size_t mwmIndex = 0; mwmIndex < mwmSignals.size(); ++mwmIndex)
  {
    auto const & mwm = mwmSignals[mwmIndex];
    int64_t const groupId = groupForMark(0, mwm.m_lat, mwm.m_lon, mwmGroupIds[mwmIndex]);
    if (!claimRepresentative(groupId)) { ++suppressed; continue; }
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(mwm.m_lat, mwm.m_lon));
    mark->SetFullScale(mode == df::Cb6SignalMode::All);
    mark->SetForward(false);
    mark->SetShowAt200m(true);
    ++created;
    ++mwmCreated;
  }
  for (int i = 0; i < n; ++i)
  {
    if (!cache.coverage.IsPointInside(mercator::FromLatLon(lats[i], lons[i]))) continue;
    bool directDuplicate = false;
    for (auto const & mwm : mwmSignals)
    {
      if (distanceMeters(mwm.m_lat, mwm.m_lon, lats[i], lons[i]) <= kDirectDuplicateM)
      {
        directDuplicate = true;
        break;
      }
    }
    if (directDuplicate) { ++suppressed; continue; }
    int64_t const groupId = groupForMark(ids[i], lats[i], lons[i], 0);
    if (!claimRepresentative(groupId)) { ++suppressed; continue; }
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(lats[i], lons[i]));
    mark->SetFullScale(mode == df::Cb6SignalMode::All);
    mark->SetForward(forward[i] == 1);
    mark->SetShowAt200m(true);
    ++created;
  }
  session.NotifyChanges();
  marksValid = true;
  renderedMode = mode;
}
