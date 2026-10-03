#include "../poi/native/convenience_brand_classifier.hpp"

#include <cassert>
#include <string>

using cb6::poi::ClassifyConvenience;
using cb6::poi::ConvenienceBrand;

int main()
{
  assert(ClassifyConvenience("7-Eleven", "", "", "").m_brand == ConvenienceBrand::SevenEleven);
  assert(ClassifyConvenience("", "", "セブン-イレブン", "").m_brand == ConvenienceBrand::SevenEleven);
  assert(ClassifyConvenience("", "FamilyMart", "", "").m_brand == ConvenienceBrand::FamilyMart);
  assert(ClassifyConvenience("", "", "ファミリーマート", "").m_brand == ConvenienceBrand::FamilyMart);
  assert(ClassifyConvenience("LAWSON", "", "", "").m_brand == ConvenienceBrand::Lawson);
  assert(ClassifyConvenience("", "", "ローソン", "").m_brand == ConvenienceBrand::Lawson);
  assert(ClassifyConvenience("", "Seicomart", "", "").m_brand == ConvenienceBrand::Seicomart);
  assert(ClassifyConvenience("", "", "セイコーマート", "").m_brand == ConvenienceBrand::Seicomart);
  assert(ClassifyConvenience("", "", "まいばすけっと", "").m_brand == ConvenienceBrand::MyBasket);
  assert(ClassifyConvenience("", "", "MINISTOP", "").m_brand == ConvenienceBrand::Ministop);
  assert(ClassifyConvenience("", "", "デイリーヤマザキ", "").m_brand == ConvenienceBrand::DailyYamazaki);
  assert(ClassifyConvenience("Lawson", "FamilyMart", "", "").m_brand == ConvenienceBrand::Lawson);
  assert(ClassifyConvenience("", "", "Unknown Local Store", "").m_brand == ConvenienceBrand::Generic);
  assert(ClassifyConvenience("", "", "Unknown Local Store", "").m_evidenceSource == "generic");
  return 0;
}
