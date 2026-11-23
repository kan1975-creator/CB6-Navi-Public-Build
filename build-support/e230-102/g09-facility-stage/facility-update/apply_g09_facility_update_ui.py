#!/usr/bin/env python3
# G09 facility-only offline update UI; stable approved GitHub Releases endpoint.
# Apply to restored CoMaps AFTER stage105 and G09 sources. No network calls at patch time.
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit('usage: apply_g09_facility_update_ui.py <comaps-root>')
root=Path(sys.argv[1])
path=root/'android/app/src/main/java/app/organicmaps/settings/Cb6DataStatusFragment.java'
if not path.is_file(): raise SystemExit('STOP_STAGE105_FRAGMENT_MISSING')
s=path.read_text()
if 'G09_FACILITY_UPDATE_WIRING' in s: raise SystemExit('STOP_ALREADY_PATCHED')
anchor='''      update.setEnabled(false);
      update.setSummary("更新先または安全な更新接続が未確定のため利用できません");'''
if s.count(anchor)!=1: raise SystemExit('STOP_UPDATE_ANCHOR_MISMATCH')
replacement='''      update.setEnabled(false);
      update.setSummary("更新先または安全な更新接続が未確定のため利用できません");
      if (kind == Kind.FACILITY_SQLITE) {
        // G09_FACILITY_UPDATE_WIRING: approved stable release URL enables manual updates.
        boolean configured = false;
        try (java.io.BufferedReader reader = new java.io.BufferedReader(
            new java.io.InputStreamReader(requireContext().getAssets().open("cb6_facilities_download.txt"),
                java.nio.charset.StandardCharsets.UTF_8))) {
          String url = reader.readLine();
          configured = "https://github.com/kan1975-creator/CB6-Navi-Public-Build/releases/latest/download/cb6_facilities.sqlite".equals(url) && reader.readLine() == null;
        } catch (java.io.IOException ignored) { /* No approved distribution endpoint. */ }
        final boolean pendingUpdate = new java.io.File(requireContext().getFilesDir(),
            "cb6_facilities.sqlite.pending").exists();
        final boolean canUpdate = configured && !pendingUpdate;
        update.setEnabled(canUpdate);
        update.setSummary(canUpdate ? "施設データを取得（次回起動時に反映）" :
            (pendingUpdate ? "更新データは次回起動時に反映" : "配信先未設定のため更新不可"));
        if (canUpdate) update.setOnPreferenceClickListener(pref -> {
          pref.setEnabled(false);
          pref.setSummary("施設データを取得しています");
          final android.content.Context appContext = requireContext().getApplicationContext();
          try {
            worker.execute(() -> {
              final boolean ok = app.organicmaps.cb6.facilities.Cb6FacilityDbDownload
                  .downloadConfigured(appContext);
              main.post(() -> {
                if (!isAdded() || getView() == null) return;
                pref.setSummary(ok ? "取得完了。次回起動時に反映" : "取得失敗。配信設定または通信を確認");
                if (!ok) pref.setEnabled(true);
                refresh();
              });
            });
          } catch (RejectedExecutionException ignored) {
            pref.setSummary("更新処理を開始できませんでした");
          }
          return true;
        });
      }'''
s=s.replace(anchor,replacement)
path.write_text(s)
print('G09_FACILITY_UPDATE_UI_PATCHED',path)
