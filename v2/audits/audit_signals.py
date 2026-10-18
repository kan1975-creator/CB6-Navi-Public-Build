#!/usr/bin/env python3
"""Gate 1 source/module/frozen-spec audit. Optional generated-atlas and APK checks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

P = argparse.ArgumentParser()
P.add_argument('root', type=Path)
P.add_argument('--atlases', action='store_true')
P.add_argument('--apk', type=Path)
P.add_argument('--allow-convenience-style', action='store_true')
args = P.parse_args()
root = args.root.resolve()
v2 = Path(__file__).resolve().parents[1]
module = v2 / 'signals'
spec = json.loads((v2/'gates/current_spec.json').read_text())['signal']

def require(ok, message):
    if not ok: raise SystemExit('SIGNAL AUDIT FAIL: ' + message)

def read(path): return (root / path).read_text()

# FAIL1/FAIL2: fixed source-preservation and 12-argument JNI invariants.
# Check transformed code semantics BEFORE generated template byte comparison.
jni_semantic = read('android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc')
mark_semantic = read('libs/map/cb6_signal_mark.hpp')
controller_semantic = read('android/app/src/main/java/app/organicmaps/cb6/signals/SignalController.java')
framework_semantic = read('android/sdk/src/main/java/app/organicmaps/sdk/Framework.java')
applier_semantic = (module/'apply_signals.py').read_text()

sym_begin = mark_semantic.find('drape_ptr<SymbolNameZoomInfo> GetSymbolNames() const override')
sym_end = mark_semantic.find('int GetMinZoom() const override', sym_begin)
require(sym_begin >= 0 and sym_end > sym_begin, 'signal zoom symbols implementation missing')
sym_shape = re.sub(r'\s+', '', mark_semantic[sym_begin:sym_end])
expected_sym = re.sub(r'\s+', '', """
drape_ptr<SymbolNameZoomInfo> GetSymbolNames() const override
{
  auto symbols = make_unique_dp<SymbolNameZoomInfo>();
  if (m_showAt200m)
    symbols->insert({15, "cb6-signal-xs"});
  if (m_forward)
  {
    symbols->insert({17, "cb6-signal-m"});
    symbols->insert({19, "cb6-signal-l"});
  }
  else
  {
    symbols->insert({17, "cb6-signal-xs"});
  }
  return symbols;
}
""")
require('symbols->insert({14,' not in mark_semantic
        and 'if(m_showAt200m)symbols->insert({15,"cb6-signal-xs"});' in sym_shape,
        '500m signal visibility not disabled')
require('symbols->insert({17,"cb6-signal-m"});' in sym_shape
        and 'symbols->insert({17,"cb6-signal-xs"});' in sym_shape,
        '100m unchanged mark restoration missing')
require(sym_shape == expected_sym, 'signal zoom symbols branch shape mismatch')
minzoom = re.search(r'int GetMinZoom\(\) const override\s*\{([^}]*)\}', mark_semantic, re.S)
require(minzoom is not None, 'signal GetMinZoom implementation missing')
min_shape = re.sub(r'\s+', '', minzoom.group(1))
require('if(m_showAt200m)return15;' in min_shape, 'minimum zoom mismatch')
require('return17;' in min_shape, '200m/100m mark zoom gating mismatch')
require(min_shape == 'if(m_showAt200m)return15;return17;',
        '200m/100m mark zoom gating mismatch')

# All twelve Java parameters and all twelve native parameters must match in type/order.
jdecl = re.search(r'public static native void nativeSetCb6Signals\s*\(([^)]*)\)\s*;', framework_semantic, re.S)
cdecl = re.search(r'JNIEXPORT void JNICALL Java_app_organicmaps_sdk_Framework_nativeSetCb6Signals\s*\(([^)]*)\)', jni_semantic, re.S)
require(jdecl is not None, 'generated JNI identity declaration missing')
require(cdecl is not None, 'JNI 12 argument order/type mismatch')
java_args = [x.strip() for x in jdecl.group(1).split(',')]
cpp_args = [x.strip() for x in cdecl.group(1).split(',')]
expected_java = [
 'double originLat', 'double originLon', 'long[] ids', 'double[] lat', 'double[] lon',
 'boolean[] forward', 'double[] memberLat', 'double[] memberLon', 'double[] centerLat',
 'double[] centerLon', 'long[] memberIds', 'long[] centerIds'
]
expected_cpp = [
 'jdouble originLat', 'jdouble originLon', 'jlongArray idArray', 'jdoubleArray latArray',
 'jdoubleArray lonArray', 'jbooleanArray forwardArray', 'jdoubleArray memberLatArray',
 'jdoubleArray memberLonArray', 'jdoubleArray centerLatArray', 'jdoubleArray centerLonArray',
 'jlongArray memberIdArray', 'jlongArray centerIdArray'
]
require(java_args == expected_java and len(java_args) == 12, 'JNI 12 argument order/type mismatch')
require(len(cpp_args) == 14 and re.fullmatch(r'JNIEnv\s*\*\s*env', cpp_args[0])
        and cpp_args[1] == 'jclass' and cpp_args[2:] == expected_cpp,
        'JNI 12 argument order/type mismatch')
identity_decl = 'public static native void nativeSetCb6Signals(' + ', '.join(expected_java) + ');'
require(identity_decl in applier_semantic, 'generated JNI identity declaration missing')
jcall = re.search(r'Framework\.nativeSetCb6Signals\s*\((.*?)\);', controller_semantic, re.S)
expected_call = ['(b[0]+b[2])/2.0', '(b[1]+b[3])/2.0', 'ids', 'lats', 'lons',
                 'forward', 'memberLats', 'memberLons', 'centerLats', 'centerLons',
                 'memberIds', 'centerIds']
require(jcall is not None and [x.strip() for x in jcall.group(1).split(',')] == expected_call,
        'JNI 12 argument order/type mismatch')
require('memberIds[i] = member.id; centerIds[i] = center.id;' in controller_semantic,
        'Java topology identity transport missing')
require('GetLongArrayRegion(memberIdArray' in jni_semantic
        and 'GetLongArrayRegion(centerIdArray' in jni_semantic,
        'JNI topology identity transport missing')

# At z17+, preserve every raw MWM mark; never normalize away MWM anchors.
require('std::vector<jlong> mwmGroupIds(mwmSignals.size(), 0);' in jni_semantic
        and 'if (!ambiguous && mappedGroup > 0) mwmGroupIds[mwmIndex] = mappedGroup;' in jni_semantic
        and 'if (mappedGroup != 0 && mappedGroup != centerIds[t])' in jni_semantic,
        'MWM ambiguous topology must preserve original marks')
mwm_start = jni_semantic.find('size_t created = 0, suppressed = 0, mwmCreated = 0;')
mwm_end = jni_semantic.find('constexpr jlong kWayIdNamespace', mwm_start)
require(mwm_start >= 0 and mwm_end > mwm_start, '100m MWM source mark restoration missing')
mwm_draw = re.sub(r'\s+', '', jni_semantic[mwm_start:mwm_end])
expected_mwm_draw = re.sub(r'\s+', '', """
size_t created = 0, suppressed = 0, mwmCreated = 0;
for (size_t mwmIndex = 0; mwmIndex < mwmSignals.size(); ++mwmIndex)
{
  auto const & mwm = mwmSignals[mwmIndex];
  auto * mark = session.CreateUserMark<Cb6SignalMark>(mercator::FromLatLon(mwm.m_lat, mwm.m_lon));
  mark->SetForward(false);
  mark->SetShowAt200m(keepAt200m(0, mwm.m_lat, mwm.m_lon, mwmGroupIds[mwmIndex]));
  ++created;
  ++mwmCreated;
}
""")
require(mwm_draw == expected_mwm_draw and 'normalizedMwmSignals' not in jni_semantic,
        '100m MWM source mark restoration missing')
require('nearby(lats[i], lons[i], cb6MwmCells' in jni_semantic
        and 'distanceMeters(mwm.m_lat, mwm.m_lon, lats[i], lons[i]) <= kDirectDuplicateM' in jni_semantic,
        'MWM/Overpass direct duplicate must use raw MWM coordinates')

# Only confirmed topology identity thins z15, unknowns stay visible.
require('std::vector<jlong> shown200mGroupIds;' in jni_semantic
        and 'if (shownId == groupId) return false;' in jni_semantic
        and 'shown200mCenters' not in jni_semantic,
        '200m confirmed-topology display gating missing')
require('if (groupId == 0) return true;' in jni_semantic
        and 'shown200mGroupIds.push_back(groupId);' in jni_semantic,
        '200m unknown or conflicting signal visibility not preserved')
require('if (matchedGroup != 0 && matchedGroup != centerIds[t]) return 0;' in jni_semantic
        and 'if (!reliableGroupId(centerIds[t])) return 0;' in jni_semantic
        and 'memberIds[t] == pointId' in jni_semantic
        and 'group.id == pointId' in jni_semantic
        and 'cb6MemberIdIndex' in jni_semantic,
        '200m intersection identity conflict not fail-open')
require('mark->SetShowAt200m(keepAt200m(0, mwm.m_lat, mwm.m_lon, mwmGroupIds[mwmIndex]));' in jni_semantic
        and 'mark->SetShowAt200m(keepAt200m(ids[i], lats[i], lons[i], 0));' in jni_semantic,
        '200m topology mark gating missing')

copies = {p: 'android/app/src/main/java/app/organicmaps/cb6/signals/' + p.name
          for p in (module / 'java').glob('*.java')}
copies[module / 'native/cb6_signal_mark.hpp'] = 'libs/map/cb6_signal_mark.hpp'
copies[module / 'native/cb6_signal_jni.inc'] = 'android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc'
for theme in ('light','dark'):
    for p in (module / 'symbols' / theme).glob('*.svg'):
        copies[p] = f'data/styles/default/{theme}/symbols/{p.name}'
for src, dst in copies.items():
    require((root/dst).read_bytes() == src.read_bytes(), 'generated template changed: ' + dst)

jni = read('android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc')
mark = read('libs/map/cb6_signal_mark.hpp')
policy = (module/'java/SignalPolicy.java').read_text()
controller = (module/'java/SignalController.java').read_text()
provider = (module/'java/OverpassSignalProvider.java').read_text()
all_module = '\n'.join(p.read_text() for p in module.rglob('*') if p.suffix in ('.java','.hpp','.inc'))
for bad in ('nativeSetCb6DrivingMarks', 'Cb6SupplementManager', 'shop=convenience', 'highway=stop', 'CB6_DRIVING'):
    require(bad not in all_module, 'legacy/unrelated feature path: ' + bad)
require(re.findall(r'ClearGroup\(UserMark::Type::(\w+)\)', jni) == ['CB6_SIGNAL'], 'publisher clears unrelated state')
require('DebugMarkPoint(pt, UserMark::Type::CB6_SIGNAL)' in mark, 'constructor/group mismatch')
require('SetIsVisible(UserMark::Type::CB6_SIGNAL, true)' in jni and 'session.NotifyChanges();' in jni, 'visibility/notification')
require('GetMarkType() const override' not in mark, 'invalid nonvirtual override')
require('SymbolIsPOI()' not in mark and 'GetDepthTestEnabled()' not in mark, 'proven direct-symbol rendering changed')
require(f"return {spec['display']['min_zoom']};" in mark, 'minimum zoom mismatch')
expected_zoom = {int(z):s for z,s in spec['display']['zoom_symbols'].items()}
expected_zoom.update({int(z):s for z,s in spec['display']['forward_zoom_symbols'].items()})
for zoom, symbol in sorted(expected_zoom.items()):
    require(f'{{{zoom}, "cb6-signal-{symbol}"}}' in mark, f'current-spec z{zoom} symbol')
require(mark.index('if (m_forward)') < mark.index('{17,'), 'unconditional enlargement')
# The scale change is a presentation-only change, not a data/source reduction.
display = spec['display']
require(display['min_zoom'] == 15 and display['full_display_min_zoom'] == 17
        and display['topology_center_match_m'] == 0.5, 'new signal zoom specification mismatch')
require(set(display['zoom_visibility']) == {'500m_or_farther', '200m', '100m_or_closer'},
        'signal visibility scale bands missing')
require('symbols->insert({14,' not in mark, '500m signal visibility not disabled')
require(f"if (m_showAt200m) return {display['min_zoom']};" in mark
        and f"return {display['full_display_min_zoom']};" in mark,
        '200m/100m mark zoom gating mismatch')
require('if (m_showAt200m)\n      symbols->insert({15, "cb6-signal-xs"});' in mark
        and 'SetShowAt200m(bool showAt200m)' in mark
        and 'm_showAt200m = showAt200m' in mark
        and 'bool m_showAt200m = true;' in mark
        and 'symbols->insert({17, "cb6-signal-xs"})' in mark,
        '100m unchanged mark restoration missing')
require('std::vector<jlong> shown200mGroupIds;' in jni
        and 'memberIds[t] == pointId' in jni
        and 'group.id == pointId' in jni
        and 'cb6GroupIndex' in jni
        and 'mwmGroupIds[mwmIndex] = mappedGroup;' in jni,
        '200m confirmed-topology display gating missing')
require('mark->SetShowAt200m(keepAt200m(0, mwm.m_lat, mwm.m_lon, mwmGroupIds[mwmIndex]));' in jni
        and 'mark->SetShowAt200m(keepAt200m(ids[i], lats[i], lons[i], 0));' in jni,
        '200m topology mark gating missing')
acq=spec['acquisition']
policy_values={
 'RADIUS_M':str(acq['radius_m']), 'MAX_POINTS':str(acq['max_points']),
 'MOVEMENT_M':str(float(acq['movement_m']))+'f', 'FORWARD_MAX_M':str(float(acq['forward_max_m']))+'f',
 'FORWARD_CONE_DEG':str(float(acq['forward_cone_deg']))+'f',
 'SOURCE_DEDUP_M':str(float(acq['source_dedup_m']))+'f'
}
for name,value in policy_values.items():
    require(f'{name} = {value}' in policy, 'current-spec constant '+name)
for token in acq['osm_queries']:
    require('['+token+']' in provider, 'current-spec query '+token)
require('new OfflineSignalProvider(' in controller and 'nativeGetCb6SignalViewportBounds()' in controller,
        'offline viewport acquisition missing')
require('new CompositeSignalProvider(' not in controller and 'new OverpassSignalProvider()' not in controller,
        'offline network fallback reintroduced')
require((module/'java/CompositeSignalProvider.java').exists() and (module/'java/VerifiedSignalProvider.java').exists(), 'supplement provider source missing')
verified = (module/'java/VerifiedSignalProvider.java').read_text()
composite = (module/'java/CompositeSignalProvider.java').read_text()
require('final String provenance, verifiedDate' in verified, 'verified supplement provenance fields missing')
require('SignalPolicy.validCoordinate(record.lat, record.lon)' in verified, 'verified supplement coordinate validation missing')
require('record.provenance == null || record.provenance.trim().isEmpty()' in verified, 'verified supplement provenance validation missing')
require('record.verifiedDate == null || !record.verifiedDate.matches' in verified, 'verified supplement date validation missing')
require('SOURCE_DEDUP_M' in composite and 'a == null && b == null' in composite, 'source dedup/fail-safe composition missing')
require('topologyMembers.addAll(a.topologyMembers)' in composite and 'new SignalSnapshot(merged, topologyMembers, topologyCenters)' in composite, 'composite drops topology normalization')
require('primaryError != null && (b == null || b.points.isEmpty())' in composite, 'primary failure can be masked by empty supplement')
require('hasBearing()' in controller and 'token != generation' in controller, 'direction/lifecycle guard')
require('snapshot.displayPoints()' in controller, 'signal display publication missing')
require('if (!active || !renderingReady || b==null) return;' in controller
        and 'Framework.nativeSetCb6Signals((b[0]+b[2])/2.0,(b[1]+b[3])/2.0,' in controller
        and 'public static native void nativeSetCb6Signals(' in applier_semantic,
        'offline viewport MWM-anchor publication missing')
snapshot = (module/'java/SignalSnapshot.java').read_text()
require('return points;' in snapshot, 'snapshot display must publish normalized retained points')
require('topologyMembers.size() - centres.size()' in snapshot, 'clustered count does not reflect topology normalization')
require('DISPLAY_CLUSTER_M' not in snapshot and 'latSum' not in snapshot and 'lonSum' not in snapshot,
        'proximity-only clustering/coordinate relocation reintroduced')
require('Executors.newSingleThreadExecutor()' in controller and 'inFlight' in controller, 'single-flight background acquisition')

# Offline-only additional guarantees: never waive original 12-argument or MWM gates.
offline_store = (module/'java/OfflineSignalStore.java').read_text()
offline_provider = (module/'java/OfflineSignalProvider.java').read_text()
builder = (module/'offline/build_hokkaido_signals.py').read_text()
offspec = spec['offline']
require(offspec['allow_network_fallback'] is False and offspec['confirmed_group_only'] is True,
        'offline immutable contract missing')
require('PUBLIC_KEY_X509_BASE64 = ""' in offline_store
        and 'if (!configured()) throw new SecurityException(' in offline_store
        and 'verifier.verify(signature)' in offline_store,
        'offline unsigned update bypass')
require('SHA256withECDSA' in offline_store and 'sqlite_sha256' in offline_store
        and 'version<=current' in offline_store and 'putString("previous", previous)' in offline_store,
        'offline signature/hash/rollback/old-db retention missing')
require('File.createTempFile(' in offline_store and 'PRAGMA integrity_check' in offline_store
        and 'signal_index' in offline_store,
        'offline database validation missing')
require('query(double south, double west, double north, double east)' in offline_store
        and 'new OfflineSignalProvider(' in controller,
        'offline viewport acquisition missing')
require('nativeGetCb6SignalViewportBounds' in jni and 'GetCurrentViewport()' in jni
        and 'nativeGetCb6SignalViewportBounds' in applier_semantic,
        'offline viewport JNI missing')
require('n > 50000' in jni and 'topologyN > 50000' in jni,
        'offline viewport data truncated')
require(spec['acquisition']['sources'] == ['osm_hokkaido_signed_offline']
        and spec['display']['ownership']['overpass_role'] == 'disabled-offline-only'
        and spec['offline']['allow_network_fallback'] is False,
        'offline authority/legacy Overpass contract mismatch')
require('cb6GroupIndex' in jni and 'cb6MemberIdIndex' in jni
        and 'cb6MemberCells' in jni and 'cb6MwmCells' in jni
        and 'shown200mIndex' in jni and 'nearby(lats[i], lons[i]' in jni,
        'offline 50k pre-indexing missing')
require('AND s.lat>=? AND s.lat<=? AND s.lon>=? AND s.lon<=?' in offline_store
        and 'ORDER BY s.id LIMIT 50001' in offline_store,
        'offline exact viewport SQL before LIMIT missing')
require('CERTIFIED_ROADS' in builder and 'node_road_ways' in builder
        and 'len(node_road_ways.get(n, ())) >= 2' in builder
        and 'TopologyWays().apply_file' in builder,
        'offline topology proof not restricted to connected road ways')
require('MAX_VIEWPORT_POINTS=50000' in snapshot and 'MAX_POINTS' not in snapshot,
        'offline viewport snapshot silently truncated')
require('FIXED_PBF_SHA256' in builder and offspec['pbf_sha256'] in builder
        and 'derive_confirmed_groups' in builder,
        'offline build provenance/topology missing')
require('OpenDocument' in applier_semantic and 'cb6_update_offline_signals' in applier_semantic
        and 'hokkaido_signals_v1.zip' in applier_semantic,
        'offline Android picker/asset injection missing')

require('main.post(() ->' in controller, 'main-thread publication')
require('[highway=traffic_signals]' in provider and '[crossing=traffic_signals]' in provider, 'road/crossing signal queries')
require('way(around:' in provider and '[crossing=traffic_signals]' in provider and ');out center geom;' in provider, 'signalized crossing way acquisition')
require('rel(around:' in provider and '[type=traffic_signals_set]' in provider, 'Japanese traffic signal set relation acquisition')
require('"relation".equals(type)' in provider and 'RELATION_ID_NAMESPACE' in provider, 'relation parser/id namespace missing')
require('e.optJSONObject("center")' in provider, 'way centre parser missing')
require('WAY_ID_NAMESPACE' in provider and 'WAY_ID_NAMESPACE | rawId' in provider, 'node/way id namespaces can collide')
require('tags.optString("highway")' in provider and 'tags.optString("crossing")' in provider and 'tags.optString("type")' in provider, 'road/crossing/signal-set parser')
require('getLatitude()' not in jni, 'invalid JNI source')
require('RectByCenterXYAndSizeInMeters(center, 3000.0)' in jni and 'mwmCreated' in jni,
        'MWM traffic-signal anchors are not published as CB6_SIGNAL')
require('kDirectDuplicateM = 0.5' in jni and 'direct-duplicate-suppressed' in jni,
        'MWM anchor priority/direct duplicate suppression missing')
require('mwmGroupIds' in jni and 'memberLats' in jni and 'centerLats' in jni,
        'confirmed topology mapping is not applied to MWM anchors')
require('distanceMeters(mwm.m_lat, mwm.m_lon, memberLats[t], memberLons[t]) > kDirectDuplicateM' in jni,
        'MWM topology mapping must use only the existing direct-match threshold')
require('TOPOLOGY_BATCH_SIZE = 64' in provider and 'nodeIds.size() == 12' not in provider,
        'topology normalization is still limited to the legacy 12-node diagnostic window')
require('applySignalNodeCenterClusterBatch' in provider and 'if (pairDistance[0] > 30.0f) continue;' in provider,
        'topology-evidence intersection normalization missing')
require('stage=topology-merged' in provider and 'fetchSignalTopologyBatch' in provider,
        'topology transport batches are not merged before intersection normalization')
require('result=topology-incomplete' in provider and 'return snapshot; // fail closed' in provider,
        'incomplete topology does not fail closed to unmerged signals')
require('stage=topology-endpoint-failed' in provider and 'ENDPOINTS.length' in provider,
        'topology endpoint fallback missing')
require('relation-normalized=' in provider and 'points.removeAll(confirmed)' in provider,
        'traffic_signals_set members are not authoritative normalization evidence')
cache = (module/'java/SignalCache.java').read_text()
require('root.optInt("schema") != 3' in cache and '.put("topology", topology)' in cache,
        'cache schema does not preserve topology normalization')
require('return new SignalSnapshot(points, members, centers)' in cache,
        'cache restore drops topology normalization')
activity = read('android/app/src/main/java/app/organicmaps/MwmActivity.java')
for hook in ('mCb6Signals.start(Map.isEngineCreated())', 'mCb6Signals.stop()', 'mCb6Signals.renderingReady()', 'mCb6Signals.onLocation(location)'):
    require(activity.count(hook) == 1, 'lifecycle hook ' + hook)
require('nativeSetCb6Signals(double originLat, double originLon, long[] ids, double[] lat, double[] lon, boolean[] forward, double[] memberLat, double[] memberLon, double[] centerLat, double[] centerLon, long[] memberIds, long[] centerIds)' in read('android/sdk/src/main/java/app/organicmaps/sdk/Framework.java'), 'Java JNI signature')
require('#include "cb6_signal_jni.inc"' in read('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp'), 'JNI translation unit')
require('CB6_SIGNAL,' in read('libs/map/user_mark.hpp'), 'type registration')
require('DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type);' in read('libs/map/user_mark.hpp'), 'typed constructor declaration')
require('DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type) : UserMark(ptOrg, type) {}' in read('libs/map/user_mark.cpp'), 'typed constructor implementation')
for theme in ('light','dark'):
    for size, dims in [('xs',('8','14')), ('s',('12','18')), ('m',('16','31')), ('l',('18','34'))]:
        svg = ET.parse(module/f'symbols/{theme}/cb6-signal-{size}.svg').getroot()
        require((svg.get('width'), svg.get('height')) == dims, 'frozen SVG dimensions')
# Stock MWM traffic-signal feature remains mapped, but CB6_SIGNAL owns visible rendering.
icons_path = 'data/styles/default/include/Icons.mapcss'
icons_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+icons_path]).decode()
stock_signal_rule = 'node|z19-[highway=traffic_signals],\n{icon-image: traffic_signals.svg}\n'
icons_expected = icons_original.replace(stock_signal_rule, '', 1)
require(icons_expected != icons_original, 'stock traffic_signals style anchor missing')
require((root/icons_path).read_text() == icons_expected, 'stock traffic_signals icon suppression is not exact')
mapping_path = 'data/mapcss-mapping.csv'
require(subprocess.check_output(['git','-C',str(root),'show','HEAD:'+mapping_path]) == (root/mapping_path).read_bytes(),
        'stock traffic_signals MWM mapping modified')

# All other protected stock functionality remains byte-identical. In the integrated
# Signal+Convenience build, permit only the exact Convenience-owned removal of the
# three pinned shop=convenience vehicle-style rules.
vehicle_icons_path = 'data/styles/vehicle/include/Icons.mapcss'
vehicle_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+vehicle_icons_path]).decode()
if args.allow_convenience_style:
    caption_selector = "node|z18-[shop=convenience],\n"
    icon_rule = """node|z17-[shop=convenience],
{icon-image: convenience-m.svg; font-size: 13.25;}
"""
    size_rule = """node|z18-[shop=convenience],
{font-size: 14.5;}
"""
    require(vehicle_original.count(caption_selector) == 2, 'convenience vehicle caption anchor changed')
    require(vehicle_original.count(icon_rule) == 1, 'convenience vehicle icon anchor changed')
    require(vehicle_original.count(size_rule) == 1, 'convenience vehicle size anchor changed')
    vehicle_expected = vehicle_original.replace(caption_selector, '', 1).replace(icon_rule, '', 1).replace(size_rule, '', 1)
    require('shop=convenience' not in vehicle_expected, 'unexpected convenience vehicle style remains after exact transform')
    require(read(vehicle_icons_path) == vehicle_expected, 'integrated convenience vehicle style change is not exact')
else:
    require(read(vehicle_icons_path) == vehicle_original, 'stock subsystem modified: ' + vehicle_icons_path)

for path in ['libs/map/bookmark_manager.cpp', 'libs/map/routing_manager.cpp',
             'android/app/src/main/java/app/organicmaps/search/SearchFragment.java']:
    original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+path])
    require(original == (root/path).read_bytes(), 'stock subsystem modified: ' + path)

symbols = ['cb6-signal-'+s for s in sorted(set(spec['display']['zoom_symbols'].values()) | set(spec['display']['forward_zoom_symbols'].values()))]
def check_atlas(data, name):
    doc = ET.fromstring(data)
    names = {e.get('name') for e in doc.iter() if e.get('name')}
    for symbol in symbols:
        require(symbol in names, name + ' missing exact symbol ' + symbol)

def check_atlas_set(entries):
    for density in ('mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi','6plus'):
        for theme in ('light','dark'):
            key = f'{density}/{theme}/symbols.sdf'
            matches = [n for n in entries if n.endswith('/'+key) or n == key]
            require(len(matches)==1, 'missing/ambiguous atlas ' + key)
            check_atlas(entries[matches[0]], matches[0])

if args.atlases:
    entries = {p.relative_to(root).as_posix():p.read_bytes() for p in (root/'data/symbols').glob('*/*/symbols.sdf')}
    check_atlas_set(entries)
    print('PASS all 12 light/dark density atlases contain every signal symbol referenced by current_spec')
if args.apk:
    with zipfile.ZipFile(args.apk) as z:
        require(z.testzip() is None, 'APK ZIP integrity')
        native = [n for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')]
        require(native and all(n.startswith('lib/arm64-v8a/') for n in native), 'arm64-only ABI')
        lib = z.read('lib/arm64-v8a/liborganicmaps.so')
        require(lib[:4] == b'\x7fELF' and lib[4:6] == b'\x02\x01' and int.from_bytes(lib[18:20],'little') == 183, 'ELF AArch64')
        require(b'Java_app_organicmaps_sdk_Framework_nativeSetCb6Signals' in lib, 'JNI symbol absent from APK native library')
        for symbol in symbols: require(symbol.encode() in lib, 'native symbol mapping absent: '+symbol)
        check_atlas_set({n:z.read(n) for n in z.namelist() if n.endswith('/symbols.sdf')})
    print('PASS APK CRC, arm64 ELF, JNI entrypoint and every packaged signal atlas')
print('PASS V2 signal specification/module/generated-source/regression audit')
