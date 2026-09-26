#!/usr/bin/env python3
"""Gate 1 source/module/frozen-spec audit. Optional generated-atlas and APK checks."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

P = argparse.ArgumentParser()
P.add_argument('root', type=Path)
P.add_argument('--atlases', action='store_true')
P.add_argument('--apk', type=Path)
args = P.parse_args()
root = args.root.resolve()
module = Path(__file__).resolve().parents[1] / 'signals'

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
require('return 14;' in mark, '1km hiding')
for zoom, symbol in [(14,'xs'), (15,'s'), (17,'m'), (19,'l')]:
    require(f'{{{zoom}, "cb6-signal-{symbol}"}}' in mark, f'frozen z{zoom} symbol')
require(mark.index('if (m_forward)') < mark.index('{17,'), 'unconditional enlargement')
for token in ('RADIUS_M = 3000', 'MAX_POINTS = 1400', 'REFRESH_MS = 45 * 1000L',
              'RETRY_MS = 12 * 1000L', 'MOVEMENT_M = 250.0f', 'FORWARD_MAX_M = 450.0f', 'FORWARD_CONE_DEG = 45.0f'):
    require(token in policy, 'frozen constant ' + token)
require('hasBearing()' in controller and 'token != generation' in controller, 'direction/lifecycle guard')
require('Executors.newSingleThreadExecutor()' in controller and 'inFlight' in controller, 'single-flight background acquisition')
require('main.post(() ->' in controller, 'main-thread publication')
require('[highway=traffic_signals]' in provider and 'tags.optString("highway")' in provider, 'real signal query/parser')
require('getLatitude()' not in jni, 'invalid JNI source')
activity = read('android/app/src/main/java/app/organicmaps/MwmActivity.java')
for hook in ('mCb6Signals.start(Map.isEngineCreated())', 'mCb6Signals.stop()', 'mCb6Signals.renderingReady()', 'mCb6Signals.onLocation(location)'):
    require(activity.count(hook) == 1, 'lifecycle hook ' + hook)
require('nativeSetCb6Signals(double[] lat, double[] lon, boolean[] forward)' in read('android/sdk/src/main/java/app/organicmaps/sdk/Framework.java'), 'Java JNI signature')
require('#include "cb6_signal_jni.inc"' in read('android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp'), 'JNI translation unit')
require('CB6_SIGNAL,' in read('libs/map/user_mark.hpp'), 'type registration')
require('DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type);' in read('libs/map/user_mark.hpp'), 'typed constructor declaration')
require('DebugMarkPoint::DebugMarkPoint(m2::PointD const & ptOrg, UserMark::Type type) : UserMark(ptOrg, type) {}' in read('libs/map/user_mark.cpp'), 'typed constructor implementation')
for theme in ('light','dark'):
    for size, dims in [('xs',('8','14')), ('s',('12','18')), ('m',('16','31')), ('l',('18','34'))]:
        svg = ET.parse(module/f'symbols/{theme}/cb6-signal-{size}.svg').getroot()
        require((svg.get('width'), svg.get('height')) == dims, 'frozen SVG dimensions')
# Stock functionality: no patch to styles/routing/search/location/bookmark implementation.
for path in ['data/styles/default/include/Icons.mapcss', 'data/styles/vehicle/include/Icons.mapcss',
             'libs/map/bookmark_manager.cpp', 'libs/map/routing_manager.cpp',
             'android/app/src/main/java/app/organicmaps/search/SearchFragment.java']:
    original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+path])
    require(original == (root/path).read_bytes(), 'stock subsystem modified: ' + path)

symbols = ['cb6-signal-'+s for s in ('xs','s','m','l')]
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
    print('PASS all 12 light/dark density atlases contain all 4 exact signal symbols')
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
