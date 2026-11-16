#include "convenience_brand_classifier.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <string>

namespace cb6::poi
{
namespace
{
std::string Normalize(std::string_view value)
{
  std::string out;
  out.reserve(value.size());
  for (unsigned char c : value)
  {
    if (c <= 0x7f)
    {
      if (std::isalnum(c))
        out.push_back(static_cast<char>(std::tolower(c)));
      continue;
    }
    out.push_back(static_cast<char>(c));
  }
  return out;
}

ConvenienceBrand Match(std::string_view raw)
{
  auto const s = Normalize(raw);
  if (s.empty())
    return ConvenienceBrand::Generic;
  auto has = [&](std::string_view token) { return s.find(token) != std::string::npos; };

  if (has("7eleven") || has("seveneleven") || has("セブンイレブン"))
    return ConvenienceBrand::SevenEleven;
  if (has("familymart") || has("ファミリーマート") || has("ファミマ"))
    return ConvenienceBrand::FamilyMart;
  if (has("lawson") || has("ローソン"))
    return ConvenienceBrand::Lawson;
  if (has("seicomart") || has("セイコーマート") || has("セコマ"))
    return ConvenienceBrand::Seicomart;
  if (has("mybasket") || has("mybasket") || has("まいばすけっと"))
    return ConvenienceBrand::MyBasket;
  if (has("ministop") || has("ミニストップ"))
    return ConvenienceBrand::Ministop;
  if (has("dailyyamazaki") || has("デイリーヤマザキ"))
    return ConvenienceBrand::DailyYamazaki;
  return ConvenienceBrand::Generic;
}
}  // namespace

ConvenienceIdentity ClassifyConvenience(std::string_view brand, std::string_view operatorName,
                                        std::string_view preferredName, std::string_view defaultName)
{
  struct Candidate { std::string_view value; char const * source; };
  std::array<Candidate, 4> const candidates = {{{brand, "brand"}, {operatorName, "operator"},
                                                {preferredName, "preferred-name"},
                                                {defaultName, "default-name"}}};
  for (auto const & candidate : candidates)
  {
    auto const result = Match(candidate.value);
    if (result != ConvenienceBrand::Generic)
      return {result, candidate.source};
  }
  return {ConvenienceBrand::Generic, "generic"};
}

char const * DebugPrint(ConvenienceBrand brand)
{
  switch (brand)
  {
  case ConvenienceBrand::SevenEleven: return "seven-eleven";
  case ConvenienceBrand::FamilyMart: return "familymart";
  case ConvenienceBrand::Lawson: return "lawson";
  case ConvenienceBrand::Seicomart: return "seicomart";
  case ConvenienceBrand::MyBasket: return "mybasket";
  case ConvenienceBrand::Ministop: return "ministop";
  case ConvenienceBrand::DailyYamazaki: return "daily-yamazaki";
  case ConvenienceBrand::Generic: return "generic";
  }
  return "generic";
}
}  // namespace cb6::poi
