package app.organicmaps.cb6.signals;

import android.content.ContentResolver;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Android Storage Access Framework import; no network or untrusted self-hash. */
public final class ManualSignalDatabaseImport {
  private static final long MAX_IMPORT_BYTES = 256L * 1024L * 1024L;
  private final Context context;
  private final SignalDatabaseActivation activation;
  private final ExecutorService io = Executors.newSingleThreadExecutor();
  private final Handler main = new Handler(Looper.getMainLooper());

  public ManualSignalDatabaseImport(Context context, SignalController controller) {
    this.context = context.getApplicationContext();
    this.activation = new SignalDatabaseActivation(this.context, controller);
  }

  /** Launch with ActivityResultLauncher<Intent> in an existing Activity.
      Its result data URI is passed to importSelected(). */
  public static Intent createPickerIntent() {
    Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
    intent.addCategory(Intent.CATEGORY_OPENABLE);
    intent.setType("application/octet-stream");
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
    return intent;
  }

  /** expectedSha256 must be independently verified, not derived from selected URI.
      Callback and controller notification are dispatched on the main thread. */
  public void importSelected(Uri selected, String expectedSha256,
      SignalDatabaseActivation.Completion completion) {
    if (selected == null || completion == null)
      throw new IllegalArgumentException("Missing selected file or completion");
    if (!ContentResolver.SCHEME_CONTENT.equals(selected.getScheme()))
      throw new IllegalArgumentException("Only content URI is accepted");
    if (expectedSha256 == null || !expectedSha256.matches("[0-9a-f]{64}"))
      throw new IllegalArgumentException("Independently verified SHA-256 required");
    io.execute(() -> {
      File imported = null;
      try {
        imported = File.createTempFile("cb6-import-", ".tmp", context.getCacheDir());
        long total = 0;
        try (InputStream in = context.getContentResolver().openInputStream(selected);
             FileOutputStream output = new FileOutputStream(imported)) {
          if (in == null) throw new IOException("Unable to open selected file");
          byte[] buffer = new byte[32768];
          int n;
          while ((n = in.read(buffer)) != -1) {
            total += n;
            if (total > MAX_IMPORT_BYTES) throw new IOException("Selected DB too large");
            output.write(buffer, 0, n);
          }
          output.getFD().sync();
        }
        File fileForActivation = imported;
        activation.activateDownloaded(fileForActivation, expectedSha256,
            new SignalDatabaseActivation.Completion() {
              @Override public void onSuccess() {
                fileForActivation.delete();
                completion.onSuccess();
              }
              @Override public void onFailure(Exception error) {
                fileForActivation.delete();
                completion.onFailure(error);
              }
            });
        imported = null; // ownership transferred to completion callback
      } catch (Exception error) {
        main.post(() -> completion.onFailure(error));
      } finally {
        if (imported != null) imported.delete();
      }
    });
  }

  public void shutdown() {
    io.shutdown();
    activation.shutdown();
  }
}
