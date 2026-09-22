#!/usr/bin/env python3
from pathlib import Path

p = Path('scripts/apply_cb6_complete.py')
s = p.read_text(encoding='utf-8')
old = '''loc_old = '''"'''"'''    dismissLocationErrorDialog();
    final RoutingController routing = RoutingController.get();
    if (!routing.isNavigating())
      return;

    RoutingInfo info = Framework.nativeGetRouteFollowingInfo();
    routing.updateCachedRoutingInfo(info);
    mNavigationController.update(info);'''"'''"'''
loc_new = '''"'''"'''    dismissLocationErrorDialog();

    if (mCb6SupplementManager != null)
      mCb6SupplementManager.onLocation(location);

    final RoutingController routing = RoutingController.get();
    if (!routing.isNavigating())
    {
      updateCb6RoadHud(Framework.nativeGetAddress(location.getLatitude(), location.getLongitude()));
      return;
    }

    RoutingInfo info = Framework.nativeGetRouteFollowingInfo();
    if (info != null)
      updateCb6RoadHud(info.currentStreet);
    routing.updateCachedRoutingInfo(info);
    mNavigationController.update(info);'''"'''"'''
s = once(s, loc_old, loc_new, "location update")'''
new = '''loc_old = '''"'''"'''    final RoutingController routing = RoutingController.get();
    if (!routing.isNavigating())
      return;

    RoutingInfo info = Framework.nativeGetRouteFollowingInfo();
    routing.updateCachedRoutingInfo(info);
    mNavigationController.update(info);'''"'''"'''
loc_new = '''"'''"'''    if (mCb6SupplementManager != null)
      mCb6SupplementManager.onLocation(location);

    final RoutingController routing = RoutingController.get();
    if (!routing.isNavigating())
    {
      updateCb6RoadHud(Framework.nativeGetAddress(location.getLatitude(), location.getLongitude()));
      return;
    }

    RoutingInfo info = Framework.nativeGetRouteFollowingInfo();
    if (info != null)
      updateCb6RoadHud(info.currentStreet);
    routing.updateCachedRoutingInfo(info);
    mNavigationController.update(info);'''"'''"'''
s = once(s, loc_old, loc_new, "location update")'''
if old not in s:
    raise SystemExit('expected location patch block not found')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('adapted apply_cb6_complete.py for pinned CoMaps')
