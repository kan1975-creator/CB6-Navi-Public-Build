#!/usr/bin/env python3
"""Audit workflow references and record/verify exact generated source identity."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('manifest', type=Path)
p.add_argument('--verify', action='store_true')
a = p.parse_args()
root = a.root.resolve()
tracked = {
 'android/app/build.gradle', 'android/app/src/main/java/app/organicmaps/MwmActivity.java',
 'android/app/src/main/res/values/strings.xml', 'android/app/src/main/res/values-ja/strings.xml',
 'android/sdk/src/main/cpp/app/organicmaps/sdk/Framework.cpp',
 'android/sdk/src/main/java/app/organicmaps/sdk/Framework.java',
 'libs/map/user_mark.hpp', 'libs/map/user_mark.cpp',
 'libs/storage/storage.cpp',
 'libs/platform/http_request.cpp',
 'android/sdk/src/main/java/app/organicmaps/sdk/downloader/ChunkTask.java',
 'data/styles/default/include/Icons.mapcss',
}
if a.verify:
    expected = json.loads(a.manifest.read_text())
    for path, sha in expected.items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != sha:
            raise SystemExit('Post-configure source changed: '+path)
    print('PASS configure did not overwrite any Gate 1 source or owned SVG')
else:
    changed = set(subprocess.check_output(['git','-C',str(root),'diff','--name-only'], text=True).splitlines())
    if changed != tracked:
        raise SystemExit('Unexpected changed upstream surfaces: '+repr(changed ^ tracked))
    new = subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard'], text=True).splitlines()
    allowed = (
      'android/app/src/main/java/app/organicmaps/cb6/signals/',
      'android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc',
      'libs/map/cb6_signal_mark.hpp',
      'data/styles/default/light/symbols/cb6-signal-',
      'data/styles/default/dark/symbols/cb6-signal-',
      'android/app/src/main/assets/cb6/hokkaido_signals_v1.zip',
    )
    if any(not x.startswith(allowed) for x in new):
        raise SystemExit('Unexpected untracked upstream surface: '+repr(new))
    # Device-test-only Sapporo z17 integrity override: permit exactly the two
    # approved storage.cpp substitutions and reject every other storage delta.
    storage = 'libs/storage/storage.cpp'
    storage_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+storage], text=True)
    storage_expected = storage_original.replace(
        '  auto const countryFile = GetCountryFile(countryId);',
        '  auto const & stockCountryFile = GetCountryFile(countryId);\n'
        '  auto countryFile = stockCountryFile;\n'
        '  bool const cb6SapporoZ17Test = type == MapFileType::Map &&\n'
        '      countryId == "Japan_Hokkaido Region_Sapporo" &&\n'
        '      !GetPlatform().CustomMapServerUrl().empty();\n'
        '  if (cb6SapporoZ17Test)\n'
        '    countryFile = platform::CountryFile(countryId, 74474156, "v/OFV+PGDp/eEWzsU/fq5VFdNp8=");', 1)
    storage_expected = storage_expected.replace(
        '                          [path = GetFileDownloadPath(countryId, fileType), sha1 = GetCountryFile(countryId).GetSha1(),',
        '                          [path = GetFileDownloadPath(countryId, fileType),\n'
        '                           sha1 = (fileType == MapFileType::Map &&\n'
        '                                   countryId == "Japan_Hokkaido Region_Sapporo" &&\n'
        '                                   !GetPlatform().CustomMapServerUrl().empty())\n'
        '                                      ? std::string("v/OFV+PGDp/eEWzsU/fq5VFdNp8=")\n'
        '                                      : GetCountryFile(countryId).GetSha1(),', 1)
    if storage_expected == storage_original or (root/storage).read_text() != storage_expected:
        raise SystemExit('Unexpected storage.cpp delta: only approved Sapporo z17 Custom Map Server integrity override is authorized')
    # Device-test-only Sapporo MWM screen diagnostics: permit exactly the
    # approved listener, HTTP fields, and Activity Toast bridge; reject all other deltas.
    chunk_task = 'android/sdk/src/main/java/app/organicmaps/sdk/downloader/ChunkTask.java'
    chunk_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+chunk_task], text=True)
    chunk_expected = chunk_original.replace(
        'class ChunkTask extends AsyncTask<Void, byte[], Integer>\n'
        '{\n'
        '  private static final String TAG = ChunkTask.class.getSimpleName();',
        'public class ChunkTask extends AsyncTask<Void, byte[], Integer>\n'
        '{\n'
        '  public interface DiagnosticListener { void onDiagnostic(String text); }\n'
        '  private static volatile DiagnosticListener sDiagnosticListener;\n'
        '  public static void setDiagnosticListener(DiagnosticListener listener) { sDiagnosticListener = listener; }\n'
        '  private String mCb6Diagnostic;\n'
        '  private static final String TAG = ChunkTask.class.getSimpleName();', 1)
    chunk_expected = chunk_expected.replace(
        '    if (!isCancelled())\n'
        '      nativeOnFinish(mHttpCallbackID, httpOrErrorCode, mBeg, mEnd);',
        '    if (!isCancelled())\n'
        '    {\n'
        '      DiagnosticListener listener = sDiagnosticListener;\n'
        '      if (listener != null && mCb6Diagnostic != null) listener.onDiagnostic(mCb6Diagnostic);\n'
        '      nativeOnFinish(mHttpCallbackID, httpOrErrorCode, mBeg, mEnd);\n'
        '    }', 1)
    chunk_expected = chunk_expected.replace(
        '      final int err = urlConnection.getResponseCode();\n'
        '      if (err == HttpURLConnection.HTTP_NOT_FOUND)',
        '      if (mUrl.contains("kan1975-creator.github.io/CB6-Navi-Public-Build/") &&\n'
        '          (mUrl.contains("Japan_Hokkaido%20Region_Sapporo.mwm") || mUrl.contains("Japan_Hokkaido Region_Sapporo.mwm")))\n'
        '        urlConnection.setRequestProperty("Accept-Encoding", "identity");\n'
        '      final int err = urlConnection.getResponseCode();\n'
        '      if (err == HttpURLConnection.HTTP_NOT_FOUND)', 1)
    chunk_expected = chunk_expected.replace(
        '      final int err = urlConnection.getResponseCode();\n'
        '      if (err == HttpURLConnection.HTTP_NOT_FOUND)',
        '      final int err = urlConnection.getResponseCode();\n'
        '      String cb6Diag = "CB6_SAPPORO_MWM_DIAG url=" + urlConnection.getURL()\n'
        '                    + "\\nhttp=" + err\n'
        '                    + " Content-Range=" + urlConnection.getHeaderField("Content-Range")\n'
        '                    + "\\nContent-Length=" + urlConnection.getHeaderField("Content-Length")\n'
        '                    + " expected=" + mExpectedFileSize\n'
        '                    + "\\nbeg=" + mBeg + " end=" + mEnd;\n'
        '      Logger.i(TAG, cb6Diag);\n'
        '      if (mUrl.contains("Japan_Hokkaido%20Region_Sapporo.mwm") || mUrl.contains("Japan_Hokkaido Region_Sapporo.mwm"))\n'
        '        mCb6Diagnostic = cb6Diag;\n'
        '      if (err == HttpURLConnection.HTTP_NOT_FOUND)', 1)
    if chunk_expected == chunk_original or (root/chunk_task).read_text() != chunk_expected:
        raise SystemExit('Unexpected ChunkTask.java delta: only approved Sapporo Custom Map Server identity encoding plus screen diagnostic listener/HTTP fields are authorized')
    activity = 'android/app/src/main/java/app/organicmaps/MwmActivity.java'
    activity_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+activity], text=True)
    activity_expected = activity_original.replace(
        '  private int mNavBarHeight;',
        '  private int mNavBarHeight;\n  private app.organicmaps.cb6.signals.SignalController mCb6Signals;', 1)
    activity_expected = activity_expected.replace(
        '    initViews(isLaunchByDeepLink);',
        '    mCb6Signals = new app.organicmaps.cb6.signals.SignalController(getApplicationContext());\n'
        '    initViews(isLaunchByDeepLink);', 1)
    activity_expected = activity_expected.replace(
        '  protected void onStart()\n'
        '  {\n'
        '    super.onStart();',
        '  protected void onStart()\n'
        '  {\n'
        '    super.onStart();\n'
        '    app.organicmaps.sdk.downloader.ChunkTask.setDiagnosticListener(text -> runOnUiThread(() ->\n'
        '        android.widget.Toast.makeText(this, text, android.widget.Toast.LENGTH_LONG).show()));\n'
        '    if (mCb6Signals != null) mCb6Signals.start(Map.isEngineCreated());', 1)
    activity_expected = activity_expected.replace(
        '  protected void onStop()\n'
        '  {\n'
        '    super.onStop();',
        '  protected void onStop()\n'
        '  {\n'
        '    app.organicmaps.sdk.downloader.ChunkTask.setDiagnosticListener(null);\n'
        '    if (mCb6Signals != null) mCb6Signals.stop();\n    super.onStop();', 1)
    activity_expected = activity_expected.replace(
        '  public void onRenderingInitializationFinished()\n'
        '  {',
        '  public void onRenderingInitializationFinished()\n'
        '  {\n'
        '    if (mCb6Signals != null) mCb6Signals.renderingReady();', 1)
    activity_expected = activity_expected.replace(
        '  public void onLocationUpdated(@NonNull Location location)\n'
        '  {',
        '  public void onLocationUpdated(@NonNull Location location)\n'
        '  {\n'
        '    if (mCb6Signals != null) mCb6Signals.onLocation(location);', 1)

    activity_expected = activity_expected.replace(
        '  private int mNavBarHeight;',
        '  private int mNavBarHeight;\n  private ActivityResultLauncher<String[]> mCb6SignalsUpdatePicker;',1)
    activity_expected = activity_expected.replace(
        '    mShareLauncher = SharingUtils.RegisterLauncher(this);',
        '    mShareLauncher = SharingUtils.RegisterLauncher(this);\n'
        '    mCb6SignalsUpdatePicker = registerForActivityResult(new ActivityResultContracts.OpenDocument(), uri -> {\n'
        '      if (uri != null && mCb6Signals != null) mCb6Signals.importSignedZip(uri, message ->\n'
        '          android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show());\n'
        '    });',1)
    activity_expected = activity_expected.replace(
        '  public void onShareLocationOptionSelected()',
        '  private void onCb6UpdateOptionSelected()\n'
        '  {\n'
        '    if (mCb6SignalsUpdatePicker != null) mCb6SignalsUpdatePicker.launch(new String[]{"application/zip", "application/octet-stream"});\n'
        '  }\n\n'
        '  public void onShareLocationOptionSelected()',1)
    activity_expected = activity_expected.replace(
        '      mDonatesUrl = Utils.getDonateUrl(getApplicationContext());',
        '      items.add(new MenuBottomSheetItem(R.string.cb6_update_offline_signals, R.drawable.ic_download,\n'
        '          this::onCb6UpdateOptionSelected));\n'
        '      mDonatesUrl = Utils.getDonateUrl(getApplicationContext());',1)
    activity_expected = activity_expected.replace(
        '  public void onShareLocationOptionSelected()',
        '  private void onCb6OsmAttributionOptionSelected()\n'
        '  {\n'
        '    new MaterialAlertDialogBuilder(this)\n'
        '        .setMessage(R.string.cb6_osm_attribution)\n'
        '        .setPositiveButton(R.string.ok, null).show();\n'
        '  }\n\n'
        '  public void onShareLocationOptionSelected()',1)
    activity_expected = activity_expected.replace(
        '      mDonatesUrl = Utils.getDonateUrl(getApplicationContext());',
        '      items.add(new MenuBottomSheetItem(R.string.cb6_osm_attribution, R.drawable.ic_logo_monochrome,\n'
        '          this::onCb6OsmAttributionOptionSelected));\n'
        '      mDonatesUrl = Utils.getDonateUrl(getApplicationContext());',1)
    for resource_path, anchor, line in (
        ('android/app/src/main/res/values/strings.xml',
         '    <string name="download_maps">Download Maps</string>',
         '    <string name="cb6_update_offline_signals">Update Hokkaido traffic signals (ZIP)</string>'),
        ('android/app/src/main/res/values-ja/strings.xml',
         '    <string name="download_maps">マップをダウンロード</string>',
         '    <string name="cb6_update_offline_signals">北海道信号機データ更新（ZIP）</string>')):
        original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+resource_path],text=True)
        expected_resource = original.replace(anchor,anchor+'\n'+line,1)
        expected_resource = expected_resource.replace(line, line+'\n'
            + '    <string name="cb6_osm_attribution">© OpenStreetMap contributors · ODbL 1.0</string>',1)
        if expected_resource == original or (root/resource_path).read_text()!=expected_resource:
            raise SystemExit('Unexpected CB6 offline string resource delta: '+resource_path)

    if activity_expected == activity_original or (root/activity).read_text() != activity_expected:
        raise SystemExit('Unexpected MwmActivity.java delta: only approved SignalController integration plus Sapporo MWM diagnostic Toast bridge is authorized')
    # Device-test-only update-check diagnostics: permit exactly the approved
    # meta/maps.json logging insertion and reject every other http_request.cpp delta.
    http_request = 'libs/platform/http_request.cpp'
    http_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+http_request], text=True)
    http_expected = http_original.replace(
        '  virtual void OnFinish(long httpOrErrorCode, int64_t, int64_t)\n'
        '  {\n'
        '    if (httpOrErrorCode == 200)',
        '  virtual void OnFinish(long httpOrErrorCode, int64_t, int64_t)\n'
        '  {\n'
        '    if (m_requestUrl.find("meta/maps.json") != string::npos)\n'
        '      LOG(LWARNING, ("CB6_SAPPORO_META_DIAG url=", m_requestUrl,\n'
        '                     " httpOrErrorCode=", httpOrErrorCode,\n'
        '                     " responseBytes=", m_downloadedData.size(),\n'
        '                     " failureReason=", non_http_error_code::DebugPrint(httpOrErrorCode)));\n'
        '    if (httpOrErrorCode == 200)', 1)
    if http_expected == http_original or (root/http_request).read_text() != http_expected:
        raise SystemExit('Unexpected http_request.cpp delta: only approved meta/maps.json diagnostic logging is authorized')
    # Signal authority: preserve MWM traffic-signal data while suppressing only its stock icon.
    icons = 'data/styles/default/include/Icons.mapcss'
    original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+icons], text=True)
    stock_signal_rule = 'node|z19-[highway=traffic_signals],\n{icon-image: traffic_signals.svg}\n'
    expected = original.replace(stock_signal_rule, '', 1)
    if expected == original or (root/icons).read_text() != expected:
        raise SystemExit('Unexpected Icons.mapcss delta: only exact stock traffic_signals icon suppression is authorized')
    mapping = 'data/mapcss-mapping.csv'
    mapping_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+mapping], text=True)
    if (root/mapping).read_text() != mapping_original:
        raise SystemExit('Unexpected mapcss-mapping.csv delta: stock traffic_signals MWM feature mapping must remain unchanged')
    hashes = {x: hashlib.sha256((root/x).read_bytes()).hexdigest() for x in sorted(tracked | set(new))}
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(hashes, indent=2)+'\n')
    print('PASS source scope: '+str(len(hashes))+' files, only identity and signals')
