#include <algorithm>
#include <cmath>
#include <cstdint>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace cb6_reset {
struct Point { int64_t id; double lat, lon; bool mwm; bool forward = false; bool vehicle = true; };
struct Member { int64_t id, center; double lat, lon, centerLat, centerLon; };
struct Result { std::vector<Point> marks; size_t rejected = 0; };
inline double meters(double a, double b, double c, double d) {
  constexpr double pi=3.14159265358979323846, r=6371000.0;
  double p=a*pi/180.0,q=c*pi/180.0,dp=(c-a)*pi/180.0,dl=(d-b)*pi/180.0;
  double x=std::sin(dp/2)*std::sin(dp/2)+std::cos(p)*std::cos(q)*std::sin(dl/2)*std::sin(dl/2);
  return 2*r*std::asin(std::min(1.0,std::sqrt(x)));
}
struct Cell { int64_t a,b; bool operator==(Cell const & x) const {return a==x.a && b==x.b;} };
struct Hash { size_t operator()(Cell const & x) const {auto a=std::hash<int64_t>{}(x.a),b=std::hash<int64_t>{}(x.b);return a^(b+size_t{0x9e3779b9}+(a<<6)+(a>>2));} };
// 0.000005 degrees: +/- 3 bins encloses 0.5 m for Hokkaido and more northerly latitudes.
constexpr double step=0.000005;
inline Cell cell(double lat,double lon){return {static_cast<int64_t>(std::floor(lat/step)),static_cast<int64_t>(std::floor(lon/step))};}
inline Result select(std::vector<Point> const & input,std::vector<Member> const & topology,bool visible){
  Result out;
  if(!visible){out.rejected=input.size();return out;}
  std::unordered_map<int64_t,Member> byId;
  std::unordered_set<int64_t> badIds,badCenters;
  std::unordered_map<int64_t,Member> centers;
  std::unordered_map<Cell,std::vector<size_t>,Hash> memberGrid;
  for(size_t i=0;i<topology.size();++i){
    auto const & m=topology[i];
    if(m.id<=0||m.center<=0||meters(m.lat,m.lon,m.centerLat,m.centerLon)>15.0)continue;
    auto it=byId.find(m.id);
    if(it==byId.end())byId.emplace(m.id,m);
    else if(it->second.center!=m.center||meters(it->second.lat,it->second.lon,m.lat,m.lon)>0.5)badIds.insert(m.id);
    auto ct=centers.find(m.center);
    if(ct==centers.end())centers.emplace(m.center,m);
    else if(meters(ct->second.centerLat,ct->second.centerLon,m.centerLat,m.centerLon)>0.5)badCenters.insert(m.center);
    memberGrid[cell(m.lat,m.lon)].push_back(i);
  }
  std::unordered_set<int64_t> claimed;
  std::unordered_map<Cell,std::vector<size_t>,Hash> selectedMwm;
  auto matchedGroup=[&](Point const & p)->int64_t{
    if(p.id>0 && !badIds.count(p.id)){
      auto it=byId.find(p.id);
      if(it!=byId.end()&&!badCenters.count(it->second.center)&&meters(p.lat,p.lon,it->second.lat,it->second.lon)<=0.5)return it->second.center;
    }
    if(!p.mwm)return 0;
    auto k=cell(p.lat,p.lon);
    int64_t group=0;
    for(int y=-3;y<=3;++y)for(int x=-3;x<=3;++x){
      auto it=memberGrid.find({k.a+y,k.b+x});
      if(it==memberGrid.end())continue;
      for(auto i:it->second){
        auto const & m=topology[i];
        if(badIds.count(m.id)||badCenters.count(m.center)||meters(p.lat,p.lon,m.lat,m.lon)>0.5)continue;
        if(group!=0&&group!=m.center)return 0;
        group=m.center;
      }
    }
    return group;
  };
  for(int pass=0;pass<2;++pass)for(auto const & p:input){
    if(p.mwm!=(pass==0))continue;
    if(!p.vehicle||!std::isfinite(p.lat)||!std::isfinite(p.lon)){++out.rejected;continue;}
    auto group=matchedGroup(p);
    if(group>0&&claimed.count(group)){++out.rejected;continue;}
    if(!p.mwm){
      bool duplicate=false;auto k=cell(p.lat,p.lon);
      for(int y=-3;y<=3&&!duplicate;++y)for(int x=-3;x<=3&&!duplicate;++x){
        auto it=selectedMwm.find({k.a+y,k.b+x});if(it==selectedMwm.end())continue;
        for(auto idx:it->second)if(meters(p.lat,p.lon,out.marks[idx].lat,out.marks[idx].lon)<=0.5){duplicate=true;break;}
      }
      if(duplicate){++out.rejected;continue;}
    }
    if(group>0)claimed.insert(group);
    if(p.mwm)selectedMwm[cell(p.lat,p.lon)].push_back(out.marks.size());
    out.marks.push_back(p);
  }
  return out;
}
}

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

  // RESET: one selection stage for MWM and supplemental signals. No fixed count cap.
  std::vector<cb6_reset::Member> topology;
  topology.reserve(topologyN);
  for (int t = 0; t < topologyN; ++t)
    topology.push_back({memberIds[t], centerIds[t], memberLats[t], memberLons[t], centerLats[t], centerLons[t]});
  std::vector<cb6_reset::Point> candidates;
  candidates.reserve(mwmSignals.size() + lats.size());
  for (auto const & mwm : mwmSignals)
    candidates.push_back({0, mwm.m_lat, mwm.m_lon, true, false, true});
  for (int i = 0; i < n; ++i)
  {
    if (!cache.coverage.IsPointInside(mercator::FromLatLon(lats[i], lons[i]))) continue;
    candidates.push_back({ids[i], lats[i], lons[i], false, forward[i] == 1, true});
  }
  auto const selected = cb6_reset::select(candidates, topology, true);
  for (auto const & p : selected.marks)
  {
    auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(p.lat, p.lon));
    mark->SetFullScale(mode == df::Cb6SignalMode::All);
    mark->SetForward(p.forward);
    mark->SetShowAt200m(true);
  }
  session.NotifyChanges();
  marksValid = true;
  renderedMode = mode;
}
