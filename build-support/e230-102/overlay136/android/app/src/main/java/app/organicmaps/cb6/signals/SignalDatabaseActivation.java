package app.organicmaps.cb6.signals;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import java.io.File;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Entry point for a DB file that has already been downloaded by an approved source. */
public final class SignalDatabaseActivation {
  private static final String DIAG_TAG = "Cb6SignalActivation";
  private final VerifiedPackageStager stager;
  private final SignalController controller;
  private final ExecutorService executor = Executors.newSingleThreadExecutor();
  private final Handler main = new Handler(Looper.getMainLooper());

  public interface Completion {
    void onSuccess();
    void onFailure(Exception error);
  }

  public SignalDatabaseActivation(android.content.Context context, SignalController controller) {
    if (controller == null) throw new IllegalArgumentException("Missing controller");
    this.stager = new VerifiedPackageStager(context.getApplicationContext());
    this.controller = controller;
  }

  /** Caller supplies the verified expected SHA-256 through a trusted channel.
      This does not download, authenticate a manifest or derive trust from the file. */
  public void activateDownloaded(File downloaded, String trustedSha256, Completion completion) {
    if (downloaded == null || completion == null)
      throw new IllegalArgumentException("Missing input");
    executor.execute(() -> {
      File staged = null;
      try {
        Log.i(DIAG_TAG, "phase=staging-start");
        staged = stager.stage(downloaded, trustedSha256);
        Log.i(DIAG_TAG, "phase=staging-complete");
        Log.i(DIAG_TAG, "phase=publication-start");
        stager.activate(staged, trustedSha256);
        Log.i(DIAG_TAG, "phase=publication-complete");
        main.post(() -> {
          controller.onSignalDatabaseActivated();
          completion.onSuccess();
        });
      } catch (Exception error) {
        Log.e(DIAG_TAG, "Activation failed", error);
        main.post(() -> completion.onFailure(error));
      } finally {
        if (staged != null && staged.exists()) staged.delete();
      }
    });
  }

  public void shutdown() { executor.shutdown(); }
}
