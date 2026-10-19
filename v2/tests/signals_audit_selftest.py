#!/usr/bin/env python3
"""Destructive proof that audit_signals.py rejects broken transformed Signal source."""
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path

P=argparse.ArgumentParser()
P.add_argument("transformed_root",type=Path)
P.add_argument("--allow-convenience-style",action="store_true")
a=P.parse_args()
ROOT=Path(__file__).resolve().parents[2]
AUDIT=ROOT/"v2/audits/audit_signals.py"
SPEC=json.loads((ROOT/"v2/gates/current_spec.json").read_text(encoding="utf-8"))
SIGNAL_SPEC=SPEC["signal"]
MIN_ZOOM=int(SIGNAL_SPEC["display"]["min_zoom"])

def run(root):
 cmd=["python3",str(AUDIT),str(root)]
 if a.allow_convenience_style: cmd.append("--allow-convenience-style")
 return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)

base=a.transformed_root.resolve()
ok=run(base)
if ok.returncode!=0:
 raise SystemExit("SIGNAL AUDIT SELFTEST BASELINE FAIL:\n"+ok.stdout+ok.stderr)

cases=[
 ("offline-viewport-jni", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "nativeGetCb6SignalViewportBounds", "nativeGetCb6DisabledViewport", "offline viewport JNI missing"),
 ("offline-no-network", "android/app/src/main/java/app/organicmaps/cb6/signals/SignalController.java",
  "new OfflineSignalProvider(", "new OfflineSignalProviderDisabled(", "offline viewport acquisition missing"),
 ("offline-signer-fail-closed", "android/app/src/main/java/app/organicmaps/cb6/signals/OfflineSignalStore.java",
  "if (!configured()) throw new SecurityException(", "if (configured()) throw new SecurityException(", "offline unsigned update bypass"),
 ("publisher-group", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "ClearGroup(UserMark::Type::CB6_SIGNAL)", "ClearGroup(UserMark::Type::DEBUG_MARK)", "publisher clears unrelated state"),
 ("symbol-zoom", "libs/map/cb6_signal_mark.hpp",
  f"return {MIN_ZOOM};", f"return {MIN_ZOOM-1};", "minimum zoom mismatch"),
 ("100m-restoration", "libs/map/cb6_signal_mark.hpp",
  "return 17;", "return 18;", "200m/100m mark zoom gating mismatch"),
 ("500m-visibility", "libs/map/cb6_signal_mark.hpp",
  'if (m_showAt200m)\n      symbols->insert({15, "cb6-signal-xs"});',
  'if (true)\n      symbols->insert({15, "cb6-signal-xs"});',
  "500m signal visibility not disabled"),
 ("200m-unknown-topology-retained", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "if (groupId == 0) return true;", "if (groupId == 0) return false;",
  "200m unknown or conflicting signal visibility not preserved"),
 ("200m-topology-center-retained", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "shown200mGroupIds.push_back(groupId);", "/* centre identity deliberately not recorded */",
  "200m unknown or conflicting signal visibility not preserved"),
 ("200m-mwm-mark-gating", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "mark->SetShowAt200m(keepAt200m(0, mwm.m_lat, mwm.m_lon, mwmGroupIds[mwmIndex]));", "mark->SetShowAt200m(true);",
  "200m topology mark gating missing"),
 ("200m-overpass-mark-gating", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "mark->SetShowAt200m(keepAt200m(ids[i], lats[i], lons[i], 0));", "mark->SetShowAt200m(true);",
  "200m topology mark gating missing"),
 ("semantic-z14-symbol", "libs/map/cb6_signal_mark.hpp",
  'if (m_showAt200m)\n      symbols->insert({15, "cb6-signal-xs"});',
  'symbols->insert({14, "cb6-signal-xs"});\n    if (m_showAt200m)\n      symbols->insert({15, "cb6-signal-xs"});',
  "500m signal visibility not disabled"),
 ("semantic-z17-restore", "libs/map/cb6_signal_mark.hpp",
  'symbols->insert({17, "cb6-signal-xs"});',
  'symbols->insert({18, "cb6-signal-xs"});',
  "100m unchanged mark restoration missing"),
 ("semantic-unknown-retained", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "if (groupId == 0) return true;", "if (groupId == 0) return false;",
  "200m unknown or conflicting signal visibility not preserved"),
 ("semantic-intersection-id-conflict", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "if (matchedGroup != 0 && matchedGroup != centerIds[t]) return 0;",
  "if (matchedGroup != 0 && matchedGroup != centerIds[t]) return matchedGroup;",
  "200m intersection identity conflict not fail-open"),
 ("semantic-member-identity", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "memberIds[t] == pointId", "memberIds[t] != pointId",
  "200m intersection identity conflict not fail-open"),
 ("semantic-mwm-ambiguous", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "if (!ambiguous && mappedGroup > 0) mwmGroupIds[mwmIndex] = mappedGroup;",
  "if (mappedGroup > 0) mwmGroupIds[mwmIndex] = mappedGroup;",
  "MWM ambiguous topology must preserve original marks"),
 ("semantic-java-identity", "android/app/src/main/java/app/organicmaps/cb6/signals/SignalController.java",
  "memberIds[i] = member.id; centerIds[i] = center.id;",
  "memberIds[i] = 0; centerIds[i] = 0;",
  "Java topology identity transport missing"),
 ("semantic-jni-identity", "android/sdk/src/main/java/app/organicmaps/sdk/Framework.java",
  "long[] memberIds, long[] centerIds);", "long[] memberIds);",
  "JNI 12 argument order/type mismatch"),
 ("semantic-mwm-original-coordinates", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "mercator::FromLatLon(mwm.m_lat, mwm.m_lon));",
  "mercator::FromLatLon(centerLats[0], centerLons[0]));",
  "100m MWM source mark restoration missing"),
 ("semantic-mwm-all-anchors", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "auto const & mwm = mwmSignals[mwmIndex];\n    auto * mark = session.CreateUserMark<Cb6SignalMark>",
  "auto const & mwm = mwmSignals[mwmIndex];\n    if (mwmGroupIds[mwmIndex] == 0) continue;\n    auto * mark = session.CreateUserMark<Cb6SignalMark>",
  "100m MWM source mark restoration missing"),
 ("semantic-mwm-raw-overpass-dedup", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "distanceMeters(mwm.m_lat, mwm.m_lon, lats[i], lons[i]) <= kDirectDuplicateM",
  "distanceMeters(centerLats[0], centerLons[0], lats[i], lons[i]) <= kDirectDuplicateM",
  "MWM/Overpass direct duplicate must use raw MWM coordinates"),
 ("semantic-jni-12-argument-order", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "jlongArray memberIdArray, jlongArray centerIdArray)",
  "jlongArray centerIdArray, jlongArray memberIdArray)",
  "JNI 12 argument order/type mismatch"),
 ("semantic-jni-12-argument-type", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "jdoubleArray memberLatArray, jdoubleArray memberLonArray",
  "jlongArray memberLatArray, jdoubleArray memberLonArray",
  "JNI 12 argument order/type mismatch"),
 ("semantic-java-12-argument-order", "android/sdk/src/main/java/app/organicmaps/sdk/Framework.java",
  "long[] memberIds, long[] centerIds);", "long[] centerIds, long[] memberIds);",
  "JNI 12 argument order/type mismatch"),
 ("stock-signal-style", "data/styles/default/include/Icons.mapcss",
  "node|z17-[highway=elevator],", "node|z16-[highway=elevator],", "stock traffic_signals icon suppression is not exact"),
 ("acquisition-query", "android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java",
  "[highway=traffic_signals]", "[highway=traffic_lights]", "current-spec query highway=traffic_signals"),
 ("topology-batch", "android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java",
  "TOPOLOGY_BATCH_SIZE = 64", "TOPOLOGY_BATCH_SIZE = 12", "topology normalization is still limited to the legacy 12-node diagnostic window"),
 ("topology-merge-before-normalize", "android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java",
  "stage=topology-merged", "stage=topology-unmerged", "topology transport batches are not merged before intersection normalization"),
 ("topology-incomplete-fail-closed", "android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java",
  "result=topology-incomplete", "result=topology-partial", "incomplete topology does not fail closed to unmerged signals"),
 ("topology-endpoint-fallback", "android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java",
  "stage=topology-endpoint-failed", "stage=topology-endpoint-error", "topology endpoint fallback missing"),
 ("mwm-topology-normalization", "android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc",
  "mwmGroupIds", "untrustedMwmGroupIds", "MWM ambiguous topology must preserve original marks"),
 ("relation-normalization", "android/app/src/main/java/app/organicmaps/cb6/signals/OverpassSignalProvider.java",
  "relation-normalized=", "relation-diagnostic-only=", "traffic_signals_set members are not authoritative normalization evidence"),
 ("composite-topology-continuity", "android/app/src/main/java/app/organicmaps/cb6/signals/CompositeSignalProvider.java",
  "topologyMembers.addAll(a.topologyMembers)", "/* topology dropped */", "composite drops topology normalization"),
 ("cache-topology-schema", "android/app/src/main/java/app/organicmaps/cb6/signals/SignalCache.java",
  "root.optInt(\"schema\") != 3", "root.optInt(\"schema\") != 2", "cache schema does not preserve topology normalization"),
 ("cache-topology-restore", "android/app/src/main/java/app/organicmaps/cb6/signals/SignalCache.java",
  "return new SignalSnapshot(points, members, centers)", "return new SignalSnapshot(points)", "cache restore drops topology normalization"),
]
if a.allow_convenience_style:
 cases.append(("integrated-convenience-style-extra", "data/styles/vehicle/include/Icons.mapcss",
               "{icon-image: ford-m.svg; icon-min-distance: 20;}", "{icon-image: ford-m.svg; icon-min-distance: 20;}\n/* unauthorized integrated style change */",
               "integrated convenience vehicle style change is not exact"))
for name,rel,old,new,needle in cases:
 with tempfile.TemporaryDirectory() as td:
  mutant=Path(td)/"comaps"
  shutil.copytree(base,mutant,symlinks=True)
  p=mutant/rel
  s=p.read_text()
  if old not in s: raise SystemExit(f"SELFTEST FIXTURE ANCHOR MISSING {name}: {old}")
  p.write_text(s.replace(old,new,1))
  cp=run(mutant)
  out=cp.stdout+cp.stderr
  if cp.returncode==0:
   raise SystemExit(f"SIGNAL AUDIT SELFTEST FAIL {name}: destructive mutation was accepted\n{out}")
  # Newly added semantic mutations MUST fail for their named invariant.
  # The generated-template byte mismatch is not sufficient as a PASS.
  semantic_only=name.startswith("semantic-")
  accepted_reasons=(needle,) if semantic_only else (needle,"generated template changed:")
  if not any(reason in out for reason in accepted_reasons):
   raise SystemExit(f"SIGNAL AUDIT SELFTEST FAIL {name}: rejected for unrecognized reason rc={cp.returncode}\n{out}")
  matched=next(reason for reason in accepted_reasons if reason in out)
  print("PASS expected signal audit rejection:",name,"->",matched)
print("CB6 SIGNAL AUDIT SELFTEST PASS: baseline accepted and destructive mutations rejected")
