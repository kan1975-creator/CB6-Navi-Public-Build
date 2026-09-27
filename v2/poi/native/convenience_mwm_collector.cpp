#include "convenience_mwm_collector.hpp"

#include "indexer/classificator.hpp"
#include "indexer/feature.hpp"
#include "map/features_fetcher.hpp"

#include "i18n/localisation.hpp"

#include <string>

namespace cb6::poi
{
namespace
{
bool IsConvenience(FeatureType & feature, uint32_t convenienceType)
{
  bool found = false;
  feature.ForEachType([&](uint32_t type)
  {
    if (type == convenienceType)
      found = true;
  });
  return found;
}

std::string Name(FeatureType & feature, int8_t lang)
{
  auto const value = feature.GetName(lang);
  return std::string(value.data(), value.size());
}
}  // namespace

std::vector<ConveniencePoi> CollectConveniencePois(FeaturesFetcher const & fetcher, m2::RectD const & rect,
                                                   int scale)
{
  std::vector<ConveniencePoi> result;
  auto const convenienceType = classif().GetTypeByPathSafe({"shop", "convenience"});
  if (convenienceType == Classificator::INVALID_TYPE)
    return result;

  fetcher.ForEachFeature(rect, [&](FeatureType & feature)
  {
    if (!IsConvenience(feature, convenienceType))
      return;

    auto const center = feature.GetCenter();
    auto const brand = feature.GetMetadata(feature::Metadata::FMD_BRAND);
    auto const operatorName = feature.GetMetadata(feature::Metadata::FMD_OPERATOR);
    auto const preferredName = Name(feature, localisation::kJapaneseLanguageIndex);
    auto const defaultName = Name(feature, localisation::kDefaultNameIndex);

    result.push_back({center.x, center.y,
                      ClassifyConvenience(brand, operatorName, preferredName, defaultName)});
  }, scale);
  return result;
}
}  // namespace cb6::poi
