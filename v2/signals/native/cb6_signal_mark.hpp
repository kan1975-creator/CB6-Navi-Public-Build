#pragma once

#include "map/user_mark.hpp"

// Dynamic Road Marks owns this type. Keep proven DebugMarkPoint rendering defaults:
// SymbolIsPOI=false takes the direct symbol path (no ordinary POI collision).
class Cb6SignalMark final : public DebugMarkPoint
{
public:
  explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt, UserMark::Type::CB6_SIGNAL) {}
  void SetForward(bool forward) { m_forward = forward; SetDirty(); }
  // Only display selection changes; all marks are retained at their source anchors.
  void SetShowAt200m(bool showAt200m) { m_showAt200m = showAt200m; SetDirty(); }

  drape_ptr<SymbolNameZoomInfo> GetSymbolNames() const override
  {
    auto symbols = make_unique_dp<SymbolNameZoomInfo>();
    if (m_showAt200m)
      symbols->insert({15, "cb6-signal-xs"});
    if (m_forward)
    {
      symbols->insert({17, "cb6-signal-m"});
      symbols->insert({19, "cb6-signal-l"});
    }
    else
    {
      symbols->insert({17, "cb6-signal-xs"});
    }
    return symbols;
  }
  int GetMinZoom() const override
  {
    if (m_showAt200m) return 15;
    return 17;
  }

private:
  bool m_forward = false;
  bool m_showAt200m = true;
};
