#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
mgr = ROOT / "android/app/src/main/java/app/organicmaps/Cb6SupplementManager.java"
fw = ROOT / "android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp"
ms = mgr.read_text(encoding="utf-8"); fs = fw.read_text(encoding="utf-8"); errors=[]
def need(text, token, label):
    if token not in text: errors.append("missing " + label + ": " + token)

for token,label in (
 ('NEAR_REFRESH_MS = 90 * 1000L','90s nearby refresh'),('NEAR_RETRY_MS = 20 * 1000L','20s failure retry'),
 ('NEAR_REFRESH_DISTANCE_M = 500.0f','500m movement refresh'),('NEAR_SIGNAL_RADIUS_M = 2000','2km lightweight radius'),
 ('requestNearbySignalsIfNeeded(lat, lon, now);','independent nearby scheduler'),
 ('private void refreshNearbySignals(double lat, double lon)','nearby fetch method'),('postQuick(endpoint, query)','short-timeout request'),
 ('c.setConnectTimeout(4000);','4s connect timeout'),('c.setReadTimeout(8000);','8s read timeout'),
 ('postNearbySignals(nearby, lat, lon);','nearby merge publish'),('mLastPublishedPoints = points.copy();','last dataset retention'),
 ('postImmediateSignals(signals);','safe immediate signal publish'),
 ('private void postImmediateSignals(@NonNull Points signals)','POI-preserving immediate publisher'),
 ('current marks preserved, retry scheduled','failure-preserve logging')): need(ms,token,label)

for endpoint in ('https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://overpass.nchc.org.tw/api/interpreter'):
    need(ms,endpoint,'fallback endpoint')

# A signal-only update must never call the whole-group postPoints publisher because
# nativeSetCb6DrivingMarks clears/rebuilds CB6_DRIVING. Require preservation of every
# non-signal kind from mLastPublishedPoints before adding fresh signals.
if 'postPoints(signals, "NET-SIG");' in ms: errors.append('unsafe signal-only whole-group publisher remains')
start=ms.find('  private void postImmediateSignals(@NonNull Points signals)'); end=ms.find('  private void postNearbySignals(',start)
if start<0 or end<0: errors.append('unable to isolate immediate signal publisher')
else:
    body=ms[start:end]
    for token in ('mLastPublishedPoints.size()','KIND_SIGNAL_FULL','KIND_SIGNAL_FORWARD','KIND_SIGNAL_CLUSTER','continue;','merged.add(mLastPublishedPoints.lat.get(i)','merged.add(signals.lat.get(i)','mLastPublishedPoints = merged.copy();','Framework.nativeSetCb6DrivingMarks(merged.lats(), merged.lons(), kindsForCurrentDirection(merged));'):
        need(body,token,'immediate signal POI preservation')

need(ms,'String poiQuery = buildPoiQuery(lat, lon);','optional POI enrichment')
if 'postImmediateSignals(signals);' in ms and 'String poiQuery = buildPoiQuery(lat, lon);' in ms and ms.index('postImmediateSignals(signals);') > ms.index('String poiQuery = buildPoiQuery(lat, lon);'):
    errors.append('immediate broad signal publish moved after POI request')

for token,label in (('KIND_SIGNAL_FORWARD = 22','kind 22'),('FORWARD_SIGNAL_MAX_M = 450.0f','450m forward limit'),('FORWARD_CONE_DEG = 45.0f','45 degree cone'),('parseSignalsNearFirst','near-first retention'),('MAX_SIGNAL_POINTS = 1400','signal cap'),('kindsForCurrentDirection(points)','direction mapping')): need(ms,token,label)
for token,label in (('class Cb6SignalMark final : public DebugMarkPoint','DebugMarkPoint signal path'),('GetMinZoom() const override { return 15; }','z15 minimum'),('symbols->insert({15, "cb6-signal"});','standard signal icon'),('symbols->insert({17, "cb6-signal-m"});','z17 forward icon'),('symbols->insert({19, "cb6-signal-l"});','z19 forward icon'),('IsNonDisplaceable() const override { return true; }','non-displaceable'),('GetDepthTestEnabled() const override { return false; }','depth disabled')): need(fs,token,label)

if errors:
 print('CB6 v1.10 AUDIT FAILED'); [print(' -',e) for e in errors]; raise SystemExit(1)
print('CB6 v1.10 AUDIT OK: signal refresh preserves convenience/stop marks and validated renderer policy')
