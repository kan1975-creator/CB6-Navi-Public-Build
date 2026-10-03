#!/usr/bin/env python3
from pathlib import Path
import re,sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve();P=[];F=[]
def check(v,m):(P if v else F).append(m)
def text(rel):
 p=ROOT/rel
 if not p.exists(): F.append('missing '+rel); return ''
 return p.read_text(encoding='utf-8',errors='replace')
mwm=text('android/app/src/main/java/app/organicmaps/MwmActivity.java');mgr=text('android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java');search=text('android/app/src/main/java/app/organicmaps/search/SearchFragment.java');vehicle=text('data/styles/vehicle/include/Icons.mapcss');fw=text('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp')
# Keep CoMaps rules intact and require CB6 building suppression at the end of each style.
for p in sorted((ROOT/'data/styles').glob('*/include/Basemap.mapcss')):
 check('CB6 runtime-final building geometry hidden' in p.read_text(encoding='utf-8'),
       'building geometry suppression: '+str(p.relative_to(ROOT)))
for p in sorted((ROOT/'data/styles').glob('*/include/Basemap_label.mapcss')):
 check('CB6 runtime-final building labels hidden' in p.read_text(encoding='utf-8'),
       'building label suppression: '+str(p.relative_to(ROOT)))
for token in ('railway=station','aeroway=aerodrome','amenity=hospital','amenity=parking','amenity=fuel','shop=supermarket','tourism=museum','amenity=community_centre','boundary=national_park','highway=speed_camera','shop=convenience'):
 check(token in vehicle,'major facility retained in vehicle style: '+token)
for token in ('CB6_POSITION_LOWER_DP = 96','updateMyPositionRoutingOffset(Math.max(0, offsetY - cb6LowerPx))','landscape ? 150 : 190','landscape ? 48 : 52','landscape ? 30 : 34','mCb6RoadHud.setTranslationX(cb6Dp(24));','info.currentStreet'):
 check(token in mwm,'UI/HUD invariant: '+token)
for token in ('scheduleCb6StartupLocationAttempt(350L);','mCb6StartupLocationRetryCount < 20','scheduleCb6StartupLocationAttempt(500L);','LocationState.nativeStartPendingPositionMode();','LocationState.nativeSwitchToNextMode();','mCb6StartupHeadingApplied || !mCb6StartupHeadingPending','mCb6StartupHeadingApplied = true;'):
 check(token in mwm,'startup invariant: '+token)
for token in ('createOnDeviceSpeechRecognizer','createSpeechRecognizer','launchCb6VoiceFallback(fallbackIntent);','@Override public void onError(int error)','intent.resolveActivity(requireContext().getPackageManager()) != null','cb6NormalizeSearchQuery','java.text.Normalizer.Form.NFKC'):
 check(token in search,'voice/fuzzy invariant: '+token)
# Keyboard, voice and show-on-map searches must all converge on the stock CoMaps
# SearchEngine. Keep the typed toolbar text/history unchanged; normalize only the query
# handed to SearchEngine. This prevents a separate CB6 search engine from drifting away
# from CoMaps result selection/routing/history behavior.
for token in (
 'SearchEngine.INSTANCE.searchInteractive(requireContext(), cb6NormalizeSearchQuery(getQuery())',
 'SearchEngine.INSTANCE.search(requireContext(), cb6NormalizeSearchQuery(getQuery())',
 'SearchEngine.INSTANCE.searchInteractive(\n        cb6NormalizeSearchQuery(query), isCategory()',
 'mToolbarController.setQuery(cb6NormalizeSearchQuery(values.get(0)))'):
 check(token in search,'unified CB6-to-CoMaps search path: '+token)
check('SearchRecents.add(query, requireContext());' in search,'stock CoMaps search history retained')
check('SearchEngine.INSTANCE.showResult(resultIndex);' in search,'stock CoMaps result-to-map path retained')
check('RoutingController.get().onPoiSelected(point);' in search,'stock CoMaps POI-to-route selection retained')
for token in ('7eleven','familymart','lawson','seicomart','ministop','dailyyamazaki','mybasket','shop=convenience','highway=stop','highway=traffic_signals','overpass-api.de','overpass.kumi.systems','overpass.nchc.org.tw','postImmediateSignals(signals);','mLastPublishedPoints = merged.copy();'):
 check(token.lower() in mgr.lower(),'supplement invariant: '+token)
check('postPoints(signals, "NET-SIG");' not in mgr,'unsafe signal-only publisher absent')
for token in ('mDiagnosticLat','mDiagnosticLon','postDiagnosticOnly','TEST1件','SIG TEST','Toast.makeText'):check(token not in mgr,'manager diagnostic absent: '+token)
for token in ('Cb6SignalDebugProbe','stockCb6->SetKind(21)','testLat = lats[n - 1]'):check(token not in fw,'native diagnostic absent: '+token)
print(f'FINAL_STATIC_CHECKS={len(P)+len(F)} PASS={len(P)} FAIL={len(F)}')
for x in P: print('PASS',x)
for x in F: print('FAIL',x)
if F: raise SystemExit(1)
