package app.organicmaps.settings;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.preference.Preference;
import app.organicmaps.R;
import app.organicmaps.cb6.data.Cb6DataStatusRepository;
import app.organicmaps.cb6.data.Cb6DataStatusRepository.Kind;
import app.organicmaps.cb6.data.Cb6DataStatusRepository.Status;

/** Safe status-only UI. Update actions are deliberately disabled until verified providers exist. */
public final class Cb6DataStatusFragment extends BaseXmlSettingsFragment {
  private Cb6DataStatusRepository repository;
  private final ExecutorService worker=Executors.newSingleThreadExecutor();
  private final Handler main=new Handler(Looper.getMainLooper());
  private int generation=0;
  @Override protected int getXmlResources() { return R.xml.cb6_data_status; }
  @Override public void onViewCreated(@NonNull View view, @Nullable Bundle state) {
    super.onViewCreated(view,state);
    repository=new Cb6DataStatusRepository(requireContext());
    for(Kind kind: Kind.values()) {
      Preference update=getPreference("cb6_update_"+kind.name().toLowerCase(java.util.Locale.ROOT));
      if (update == null) continue;
      update.setEnabled(false);
      update.setSummary("更新先または安全な更新接続が未確定のため利用できません");
    }
  }
  @Override public void onResume() { super.onResume(); if(repository!=null) refresh(); }
  @Override public void onDestroy() {
    generation++;
    worker.shutdownNow();
    super.onDestroy();
  }
  private void refresh() {
    final int token=++generation;
    // MapManager is @UiThread; its JNI Storage calls must not run on worker.
    final Status mwm=repository.get(Kind.MWM);
    if(token==generation && isAdded() && getView()!=null) show(mwm);
    try {
      worker.execute(() -> {
        for(Kind kind: Kind.values()) {
          if(kind==Kind.MWM) continue;
          final Status s=repository.get(kind);
          main.post(() -> {
            if(token==generation && isAdded() && getView()!=null) show(s);
          });
        }
      });
    } catch (RejectedExecutionException ignored) {
      // The fragment is being destroyed; discard this refresh request.
    }
  }
  private void show(Status s) {
      Kind kind=s.kind;
      Preference p=getPreference("cb6_status_"+kind.name().toLowerCase(java.util.Locale.ROOT));
      if (p == null) return;
      StringBuilder summary=new StringBuilder("状態: ").append(s.phase.name());
      if(s.detail!=null && !s.detail.isEmpty()) summary.append(" ／ ").append(s.detail);
      if(s.downloadedBytes>=0) summary.append(" ／ ").append(s.downloadedBytes).append(" bytes");
      if(s.totalBytes>0 && s.downloadedBytes>=0 && s.downloadedBytes<=s.totalBytes)
        summary.append(" (").append(s.downloadedBytes*100/s.totalBytes).append("%)");
      if(s.count>=0) summary.append(" ／ 件数: ").append(s.count);
      if(s.updatedAt>0) summary.append(" ／ ファイル更新: ").append(new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm",java.util.Locale.JAPAN).format(new java.util.Date(s.updatedAt)));
      if(s.version!=null && !s.version.isEmpty()) summary.append(" ／ 版: ").append(s.version);
      if(s.error!=null && !s.error.isEmpty()) summary.append(" ／ エラー: ").append(s.error);
      p.setSummary(summary.toString());
  }
}
