#pragma once

#include "convenience_brand_classifier.hpp"

#include <vector>

class FeaturesFetcher;
namespace m2 { class RectD; }

namespace cb6::poi
{
struct ConveniencePoi
{
  double m_mercatorX = 0.0;
  double m_mercatorY = 0.0;
  ConvenienceIdentity m_identity;
};

std::vector<ConveniencePoi> CollectConveniencePois(FeaturesFetcher const & fetcher, m2::RectD const & rect,
                                                   int scale);
}  // namespace cb6::poi
