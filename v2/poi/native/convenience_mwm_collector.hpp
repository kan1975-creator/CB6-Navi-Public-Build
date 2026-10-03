#pragma once

#include "convenience_brand_classifier.hpp"
#include "geometry/rect2d.hpp"

#include <vector>

class DataSource;

namespace cb6::poi
{
struct ConveniencePoi
{
  double m_mercatorX = 0.0;
  double m_mercatorY = 0.0;
  ConvenienceIdentity m_identity;
};

std::vector<ConveniencePoi> CollectConveniencePois(DataSource const & dataSource, m2::RectD const & rect,
                                                   int scale);
}  // namespace cb6::poi
