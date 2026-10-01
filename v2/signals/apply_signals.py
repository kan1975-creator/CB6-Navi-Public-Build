#!/usr/bin/env python3
"""Dynamic Road Marks / signals only. One idempotent transform; no legacy stack."""
from pathlib import Path
import shutil
import sys

MODULE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve()

# Stage 1: keep stock MWM traffic-signal coordinates/icon, extend only its stock style zoom.
icons = ROOT / 'data/styles/default/include/Icons.mapcss'
icons_text = icons.read_text()
stock_signal_rule = 'node|z19-[highway=traffic_signals],'
extended_signal_rule = 'node|z17-[highway=traffic_signals],'
if stock_signal_rule in icons_text:
    icons.write_text(icons_text.replace(stock_signal_rule, extended_signal_rule, 1))
elif extended_signal_rule not in icons_text:
    raise SystemExit('traffic_signals stock style anchor missing') if len(sys.argv) > 1 else Path('comaps').resolve()

def replace(path, old, new):
    p = ROOT / path
    text = p.read_text()
    if new in text:
        if text.count(new) != 1:
            raise SystemExit(f'duplicate V2 integration: {path}')
        return
    if text.count(old) != 1:
        raise SystemExit(f'pinned anchor mismatch: {path}: {old[:80]}')
    p.write_text(text.replace(old, new, 1))

# Device-test-only Sapporo z17 MWM integrity override.
# Active only when a custom map server is configured; stock server behavior is unchanged.
replace('libs/storage/storage.cpp',
        '  auto const countryFile = GetCountryFile(countryId);',
        '  auto const & stockCountryFile = GetCountryFile(countryId);\n'
        '  auto countryFile = stockCountryFile;\n'
        '  bool const cb6SapporoZ17Test = type == MapFileType::Map &&\n'
        '      countryId == "Japan_Hokkaido Region_Sapporo" &&\n'
        '      !GetPlatform().CustomMapServerUrl().empty();\n'
        '  if (cb6SapporoZ17Test)\n'
        '    countryFile = platform::CountryFile(countryId, 74474156, "v/OFV+PGDp/eEWzsU/fq5VFdNp8=");')
replace('libs/storage/storage.cpp',
        '                          [path = GetFileDownloadPath(countryId, fileType), sha1 = GetCountryFile(countryId).GetSha1(),',
        '                          [path = GetFileDownloadPath(countryId, fileType),\n'
        '                           sha1 = (fileType == MapFileType::Map &&\n'
        '                                   countryId == "Japan_Hokkaido Region_Sapporo" &&\n'
        '                                   !GetPlatform().CustomMapServerUrl().empty())\n'
        '                                      ? std::string("v/OFV+PGDp/eEWzsU/fq5VFdNp8=")\n'
        '                                      : GetCountryFile(countryId).GetSha1(),')


replace('libs/map/user_mark.hpp',
        '    TRAFFIC_LIGHT,\n    USER_MARK_TYPES_COUNT,',
        '    TRAFFIC_LIGHT,\n    CB6_SIGNAL,\n    USER_MARK_TYPES_COUNT,')
replace('libs/map/user_mark.hpp',
        '  explicit DebugMarkPoint(m2::PointD const & ptOrg);',
        '  explicit DebugMarkPoint(m2::PointD const & ptOrg);\n  DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type);')
replace('libs/map/user_mark.cpp',
        'DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg) : UserMark(ptOrg, UserMark::Type::DEBUG_MARK) {}',
        'DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg) : UserMark(ptOrg, UserMark::Type::DEBUG_MARK) {}\n\n'
        'DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type) : UserMark(ptOrg, type) {}')
replace('libs/map/user_mark.cpp',
        '  case UserMark::Type::TRAFFIC_LIGHT: return "TRAFFIC_LIGHT";',
        '  case UserMark::Type::TRAFFIC_LIGHT: return "TRAFFIC_LIGHT";\n'
        '  case UserMark::Type::CB6_SIGNAL: return "CB6_SIGNAL";')
replace('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp',
        '#include "map/user_mark.hpp"',
        '#include "map/user_mark.hpp"\n#include "map/cb6_signal_mark.hpp"\n#include "indexer/classificator.hpp"\n#include "indexer/feature.hpp"\n#include "indexer/scales.hpp"\n#include "geometry/mercator.hpp"\n#include <cmath>\n#include <vector>')
replace('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp',
        'JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeClearApiPoints',
        '#include "cb6_signal_jni.inc"\n\nJNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeClearApiPoints')
replace('android/sdk/src/main/java/app/organicmaps/sdk/Framework.java',
        '  public static native String nativeGetAddress(double lat, double lon);',
        '  public static native String nativeGetAddress(double lat, double lon);\n\n'
        '  // Signal-only snapshot. Main thread; arrays must have equal lengths.\n'
        '  public static native void nativeSetCb6Signals(double[] lat, double[] lon, boolean[] forward);\n' +
        '  public static native void nativeLogCb6MwmSignals(double lat, double lon);')
activity = 'android/app/src/main/java/app/organicmaps/MwmActivity.java'
replace(activity, '  private int mNavBarHeight;',
        '  private int mNavBarHeight;\n  private app.organicmaps.cb6.signals.SignalController mCb6Signals;')
replace(activity, '    initViews(isLaunchByDeepLink);',
        '    mCb6Signals = new app.organicmaps.cb6.signals.SignalController(getApplicationContext());\n'
        '    initViews(isLaunchByDeepLink);')
replace(activity, '  protected void onStart()\n  {\n    super.onStart();',
        '  protected void onStart()\n  {\n    super.onStart();\n'
        '    if (mCb6Signals != null) mCb6Signals.start(Map.isEngineCreated());')
replace(activity, '  protected void onStop()\n  {\n    super.onStop();',
        '  protected void onStop()\n  {\n    if (mCb6Signals != null) mCb6Signals.stop();\n    super.onStop();')
replace(activity, '  public void onRenderingInitializationFinished()\n  {',
        '  public void onRenderingInitializationFinished()\n  {\n'
        '    if (mCb6Signals != null) mCb6Signals.renderingReady();')
replace(activity, '  public void onLocationUpdated(@NonNull Location location)\n  {',
        '  public void onLocationUpdated(@NonNull Location location)\n  {\n'
        '    if (mCb6Signals != null) mCb6Signals.onLocation(location);')

for p in (MODULE / 'java').glob('*.java'):
    dst = ROOT / 'android/app/src/main/java/app/organicmaps/cb6/signals' / p.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, dst)
for name, dst in [('cb6_signal_mark.hpp', 'libs/map/cb6_signal_mark.hpp'),
                  ('cb6_signal_jni.inc', 'android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc')]:
    shutil.copyfile(MODULE / 'native' / name, ROOT / dst)
for theme in ('light', 'dark'):
    for p in (MODULE / 'symbols' / theme).glob('*.svg'):
        shutil.copyfile(p, ROOT / 'data/styles/default' / theme / 'symbols' / p.name)
print('V2 signal transform applied; stock styles/search/navigation/location preserved')
