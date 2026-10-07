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
require('new CompositeSignalProvider(' in controller and 'new VerifiedSignalProvider()' in controller, 'composite/supplement acquisition not wired')
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
require('location == null' in controller and 'nativeSetCb6Signals(location.getLatitude(), location.getLongitude(),' in controller,
        'MWM-anchor publication must run from current location even with empty Overpass snapshot')
snapshot = (module/'java/SignalSnapshot.java').read_text()
require('return points;' in snapshot, 'snapshot display must publish normalized retained points')
require('topologyMembers.size() - centres.size()' in snapshot, 'clustered count does not reflect topology normalization')
require('DISPLAY_CLUSTER_M' not in snapshot and 'latSum' not in snapshot and 'lonSum' not in snapshot,
        'proximity-only clustering/coordinate relocation reintroduced')
require('Executors.newSingleThreadExecutor()' in controller and 'inFlight' in controller, 'single-flight background acquisition')
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
require('normalizedMwmSignals' in jni and 'memberLats' in jni and 'centerLats' in jni,
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
require('nativeSetCb6Signals(double originLat, double originLon, long[] ids, double[] lat, double[] lon, boolean[] forward, double[] memberLat, double[] memberLon, double[] centerLat, double[] centerLon)' in read('android/sdk/src/main/java/app/organicmaps/sdk/Framework.java'), 'Java JNI signature')
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
