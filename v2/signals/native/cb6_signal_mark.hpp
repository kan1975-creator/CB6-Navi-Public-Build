#pragma once

#include "map/user_mark.hpp"

// Dynamic Road Marks owns this type. Keep proven DebugMarkPoint rendering defaults:
// SymbolIsPOI=false takes the direct symbol path (no ordinary POI collision).
class Cb6SignalMark final : public DebugMarkPoint
{
public:
  explicit Cb6SignalMark(m2::PointD const & pt) : DebugMarkPoint(pt, UserMark::Type::CB6_SIGNAL) {}
  void SetForward(bool forward) { m_forward = forward; SetDirty(); }

  drape_ptr<SymbolNameZoomInfo> GetSymbolNames() const override
  {
    auto symbols = make_unique_dp<SymbolNameZoomInfo>();
    symbols->insert({14, "cb6-signal-xs"});
    symbols->insert({15, "cb6-signal-xs"});
    if (m_forward)
    {
      symbols->insert({17, "cb6-signal-m"});
      symbols->insert({19, "cb6-signal-l"});
    }
    return symbols;
  }
  int GetMinZoom() const override { return 14; }

private:
  bool m_forward = false;
};
