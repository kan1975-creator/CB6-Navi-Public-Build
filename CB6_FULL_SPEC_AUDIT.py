#!/usr/bin/env python3
from pathlib import Path
import sys, zipfile, xml.etree.ElementTree as ET
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('comaps').resolve(); APK=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else None
PASS=[];FAIL=[]
def check(c,m):(PASS if c else FAIL).append(m)
def text(rel):
 p=ROOT/rel
 if not p.exists(): FAIL.append('missing: '+rel);return ''
 return p.read_text(encoding='utf-8',errors='replace')
gradle=text('android/app/build.gradle');check("project.ext.appId = 'jp.cb6.navi'" in gradle,'independent applicationId jp.cb6.navi');check("project.ext.appName = 'CB6 Navi'" in gradle,'CB6 Navi app name')
mwm=text('android/app/src/main/java/app/organicmaps/MwmActivity.java');check('Locale.JAPAN' not in mwm and 'forceCb6JapaneseLocale' not in mwm,'no forced Japanese locale regression')
for rel in ('libs/drape_frontend/my_position.cpp','data/styles/default/light/symbols/current-position.svg','data/styles/default/dark/symbols/current-position.svg'):
 s=text(rel);check('CB6' not in s and 'cb6' not in s,'stock own-position untouched: '+rel)
styles='\n'.join(p.read_text(encoding='utf-8',errors='replace') for p in ROOT.glob('data/styles/**/*.mapcss'));check('[building][addr:housenumber]' in styles,'building address-number suppression present');check('[entrance][addr:housenumber]' not in styles,'unsafe entrance address rule absent');check('place=quarter' in styles and 'place=neighbourhood' in styles,'fine locality suppression present')
mgr=text('android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java');mgr_l=mgr.lower()
for token in ('highway=traffic_signals','highway=stop','shop=convenience','7eleven','familymart','lawson','seicomart','ministop','dailyyamazaki','mybasket','overpass-api.de','overpass.kumi.systems'):check(token in mgr_l,'supplement manager token: '+token)
for token in ('amenity=fuel','amenity=hospital','shop=supermarket'):check(token not in mgr_l,'stock CoMaps POI path not duplicated: '+token)
for token in ('NEAR_REFRESH_MS = 45 * 1000L','NEAR_RETRY_MS = 12 * 1000L','NEAR_REFRESH_DISTANCE_M = 250.0f','NEAR_SIGNAL_RADIUS_M = 3000','requestNearbySignalsIfNeeded(lat, lon, now);','postNearbySignals(nearby, lat, lon);','mLastPublishedPoints','overpass.nchc.org.tw'):check(token in mgr,'signal acquisition resilience: '+token)
for token in ('KIND_SIGNAL_FORWARD = 22','FORWARD_SIGNAL_MAX_M = 450.0f','FORWARD_CONE_DEG = 45.0f'):check(token in mgr,'forward signal policy: '+token)
check('postImmediateSignals(signals);' in mgr,'signal immediate refresh uses preserving publisher');check('private void postImmediateSignals(@NonNull Points signals)' in mgr,'POI-preserving immediate publisher exists');check('postPoints(signals, "NET-SIG");' not in mgr,'unsafe signal-only whole-group publisher absent');check('mLastPublishedPoints = merged.copy();' in mgr,'merged CB6 dataset retained after signal refresh')
check('ThemeSwitcher.INSTANCE.restart(true);' in mwm,'renderer/theme restart present');check('refreshCb6FromSavedLocation();' in mwm,'saved GPS refresh after renderer restart');check(mwm.count('mCb6SupplementManager.reapplySavedMarks();')>=2,'saved CB6 marks re-applied at least twice');check('1800L' in mwm,'first delayed mark reapply at 1.8s');check('5000L' in mwm,'second delayed mark reapply at 5.0s');check('public void reapplySavedMarks()' in mgr,'supplement manager exposes mark reapply')
fwcpp=text('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp')
for token in ('class Cb6SignalMark final : public DebugMarkPoint','DebugMarkPoint(pt, UserMark::Type::CB6_DRIVING)','GetMinZoom() const override { return 14; }','symbols->insert({14, "cb6-signal-xs"});','symbols->insert({15, "cb6-signal-s"});','symbols->insert({17, "cb6-signal-m"});','symbols->insert({19, "cb6-signal-l"});','IsNonDisplaceable() const override { return true; }','GetDepthTestEnabled() const override { return false; }','session.ClearGroup(UserMark::Type::CB6_DRIVING);','session.SetIsVisible(UserMark::Type::CB6_DRIVING, true);','session.CreateUserMark<Cb6SignalMark>(pt)','session.NotifyChanges();'):check(token in fwcpp,'signal renderer: '+token)
for p in sorted((ROOT/'data/styles').glob('*/include/Icons.mapcss')):check('[highway=traffic_signals]' not in p.read_text(encoding='utf-8',errors='replace'),'native MapCSS signal disabled: '+str(p.relative_to(ROOT)))
fwjava=text('android/sdk/src/main/java/app/organicmaps/sdk/Framework.java');user_h=text('libs/map/user_mark.hpp');user=text('libs/map/user_mark.cpp');check('CB6_DRIVING' in user_h and 'USER_MARK_TYPES_COUNT' in user_h,'CB6_DRIVING user-mark type declared');check('nativeSetCb6DrivingMarks' in fwjava,'CB6 JNI Java declaration');check('Java_app_organicmaps_sdk_Framework_nativeSetCb6DrivingMarks' in fwcpp,'CB6 JNI C++ implementation');check('Framework.nativeSetCb6DrivingMarks' in mgr,'supplement manager publishes marks through JNI')
for name in ('seven','familymart','lawson','seicomart','ministop','daily','mybasket'):check('cb6-'+name in user or 'cb6-'+name in fwcpp,'brand renderer mapping: '+name)
check('cb6-stop' in user or 'cb6-stop' in fwcpp,'stop-sign renderer mapping')
needed=['cb6-stop.svg','cb6-stop-l.svg','cb6-signal.svg','cb6-signal-s.svg','cb6-signal-m.svg','cb6-signal-l.svg','cb6-seven.svg','cb6-familymart.svg','cb6-lawson.svg','cb6-seicomart.svg','cb6-ministop.svg','cb6-daily.svg','cb6-mybasket.svg','cb6-convenience.svg']
for theme in ('light','dark'):
 for name in needed:
  p=ROOT/'data/styles/default'/theme/'symbols'/name
  if not p.exists():FAIL.append('missing icon: '+theme+'/'+name);continue
  try:ET.parse(p);PASS.append('valid SVG: '+theme+'/'+name)
  except Exception as e:FAIL.append('invalid SVG '+theme+'/'+name+': '+str(e))
vehicle=text('data/styles/vehicle/include/Icons.mapcss')
for token in ('shop=convenience','amenity=fuel','shop=supermarket','highway=speed_camera','railway=station','aeroway=aerodrome','amenity=hospital','amenity=parking'):check(token in vehicle,'stock vehicle POI retained: '+token)
for token in ('cb6_road_hud','cb6_google_maps','CB6_POSITION_LOWER_DP = 96','mCb6SupplementManager.onLocation','info.currentStreet','mCb6RoadHud.setTranslationX(cb6Dp(24));','scheduleCb6StartupLocationMode();','applyCb6StartupHeadingIfReady();','LocationState.nativeStartPendingPositionMode();','LocationState.nativeSwitchToNextMode();','scheduleCb6StartupLocationAttempt(350L);','mCb6StartupLocationRetryCount < 20','scheduleCb6StartupLocationAttempt(500L);'):check(token in mwm,'map UI/startup: '+token)
check('updateMyPositionRoutingOffset(Math.max(0, offsetY - cb6LowerPx))' in mwm,'lower navigation own-position offset');check('landscape ? 150 : 190' in mwm,'road HUD compact width retained');check('landscape ? 12 : 13' in mwm,'road HUD compact text size retained');check('landscape ? 48 : 52' in mwm,'Google helper compact width retained');check('landscape ? 30 : 34' in mwm,'Google helper compact bottom-right placement');check(mwm.count('applyCb6StartupHeadingIfReady();')>=2,'startup heading transition has retry/event path');check('mCb6StartupHeadingApplied' in mwm,'startup heading transition is idempotent')
layout=text('android/app/src/main/res/layout/activity_map.xml');check('android:id="@+id/cb6_road_hud"' in layout,'road-name HUD view');check('android:id="@+id/cb6_google_maps"' in layout,'Google Maps helper view')
try:ET.parse(ROOT/'android/app/src/main/res/layout/activity_map.xml');PASS.append('activity_map.xml well formed')
except Exception as e:FAIL.append('activity_map.xml parse: '+str(e))
manifest=text('android/app/src/main/AndroidManifest.xml');input_utils=text('android/app/src/main/java/app/organicmaps/util/InputUtils.java');search=text('android/app/src/main/java/app/organicmaps/search/SearchFragment.java')
for token in ('android.permission.RECORD_AUDIO','android.speech.action.RECOGNIZE_SPEECH','android.speech.RecognitionService'):check(token in manifest,'voice manifest: '+token)
for token in ('mVoiceInputSupported = true; // CB6:','RecognizerIntent.EXTRA_LANGUAGE, "ja-JP"','RecognizerIntent.EXTRA_MAX_RESULTS, 3'):check(token in input_utils,'voice input helper: '+token)
for token in ('SpeechRecognizer.isOnDeviceRecognitionAvailable(requireContext())','SpeechRecognizer.createOnDeviceSpeechRecognizer(requireContext())','SpeechRecognizer.createSpeechRecognizer(requireContext())','SpeechRecognizer.isRecognitionAvailable(requireContext())','mCb6AudioPermissionLauncher','RecognizerIntent.EXTRA_LANGUAGE, "ja-JP"','cb6NormalizeSearchQuery(values.get(0))','java.text.Normalizer.Form.NFKC','"セイコマ", "セイコーマート"','"ファミマ", "ファミリーマート"','"ガソスタ", "ガソリンスタンド"','SearchEngine.INSTANCE.searchInteractive(requireContext(), cb6NormalizeSearchQuery(getQuery())','SearchEngine.INSTANCE.search(requireContext(), cb6NormalizeSearchQuery(getQuery())','SearchEngine.INSTANCE.searchInteractive(\n        cb6NormalizeSearchQuery(query), isCategory()','SearchRecents.add(query, requireContext());','SearchEngine.INSTANCE.showResult(resultIndex);','RoutingController.get().onPoiSelected(point);'):check(token in search,'voice/fuzzy/stock-search integration: '+token)
for token in ('nativeHasSavedRoutePoints','nativeLoadRoutePoints','nativeSetAutoReroute'):check(token in fwjava,'navigation continuity API retained: '+token)
if APK is not None:
 check(APK.exists(),'final APK exists')
 if APK.exists():
  try:
   with zipfile.ZipFile(APK,'r') as z:
    names=z.namelist();check(any('assets/drules_proto_vehicle' in n for n in names),'APK contains vehicle drules');check(any('assets/symbols/' in n and n.endswith('symbols.sdf') for n in names),'APK contains symbol atlases')
    needles=[b'cb6-seven',b'cb6-familymart',b'cb6-lawson',b'cb6-seicomart',b'cb6-ministop',b'cb6-daily',b'cb6-mybasket',b'cb6-convenience',b'cb6-signal',b'cb6-signal-m',b'cb6-signal-l',b'cb6-stop',b'ja-JP',b'RECORD_AUDIO',b'Cb6SupplementManager',b'SpeechRecognizer'];found={n:False for n in needles}
    for member in names:
     try:data=z.read(member)
     except Exception:continue
     for needle in needles:
      if not found[needle] and needle in data:found[needle]=True
    for needle,ok in found.items():check(ok,'APK payload token: '+needle.decode('utf-8',errors='replace'))
  except Exception as e:FAIL.append('APK inspection failed: '+str(e))
print(f'FULL_SPEC_CHECKS={len(PASS)+len(FAIL)} PASS={len(PASS)} FAIL={len(FAIL)}')
for x in PASS:print('PASS',x)
for x in FAIL:print('FAIL',x)
if FAIL:raise SystemExit(1)
