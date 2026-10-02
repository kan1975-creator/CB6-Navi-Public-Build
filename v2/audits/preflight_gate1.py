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
        raise SystemExit('Unexpected ChunkTask.java delta: only approved Sapporo MWM screen diagnostic listener/HTTP fields are authorized')
    activity = 'android/app/src/main/java/app/organicmaps/MwmActivity.java'
    activity_original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+activity], text=True)
    activity_expected = activity_original.replace(
        '  protected void onStart()\n'
        '  {\n'
        '    super.onStart();',
        '  protected void onStart()\n'
        '  {\n'
        '    super.onStart();\n'
        '    app.organicmaps.sdk.downloader.ChunkTask.setDiagnosticListener(text -> runOnUiThread(() ->\n'
        '        android.widget.Toast.makeText(this, text, android.widget.Toast.LENGTH_LONG).show()));', 1)
    activity_expected = activity_expected.replace(
        '  protected void onStop()\n'
        '  {\n'
        '    super.onStop();',
        '  protected void onStop()\n'
        '  {\n'
        '    app.organicmaps.sdk.downloader.ChunkTask.setDiagnosticListener(null);\n'
        '    super.onStop();', 1)
    if activity_expected == activity_original or (root/activity).read_text() != activity_expected:
        raise SystemExit('Unexpected MwmActivity.java delta: only approved Sapporo MWM diagnostic Toast bridge is authorized')
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
    # Stage-1 Signal authority permits exactly the stock traffic_signals z19 -> z17 delta.
    icons = 'data/styles/default/include/Icons.mapcss'
    original = subprocess.check_output(['git','-C',str(root),'show','HEAD:'+icons], text=True)
    expected = original.replace('node|z19-[highway=traffic_signals],', 'node|z17-[highway=traffic_signals],', 1)
    if expected == original or (root/icons).read_text() != expected:
        raise SystemExit('Unexpected Icons.mapcss delta: only traffic_signals z19-to-z17 is authorized')
    hashes = {x: hashlib.sha256((root/x).read_bytes()).hexdigest() for x in sorted(tracked | set(new))}
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(hashes, indent=2)+'\n')
    print('PASS source scope: '+str(len(hashes))+' files, only identity and signals')
