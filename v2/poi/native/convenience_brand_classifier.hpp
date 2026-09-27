#pragma once

#include <string>
#include <string_view>

namespace cb6::poi
{
enum class ConvenienceBrand
{
  SevenEleven,
  FamilyMart,
  Lawson,
  Seicomart,
  MyBasket,
  Ministop,
  DailyYamazaki,
  Generic
};

struct ConvenienceIdentity
{
  ConvenienceBrand m_brand = ConvenienceBrand::Generic;
  std::string m_evidenceSource;
};

ConvenienceIdentity ClassifyConvenience(std::string_view brand, std::string_view operatorName,
                                        std::string_view preferredName, std::string_view defaultName);
char const * DebugPrint(ConvenienceBrand brand);
}  // namespace cb6::poi
