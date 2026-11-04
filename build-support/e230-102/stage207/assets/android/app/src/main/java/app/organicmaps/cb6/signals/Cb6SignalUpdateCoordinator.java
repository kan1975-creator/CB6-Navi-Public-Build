package app.organicmaps.cb6.signals;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import java.io.File;
import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;
import org.json.JSONObject;
import org.bouncycastle.math.ec.rfc8032.Ed25519;
/** Isolated candidate: production deployment blocked pending dependencies and durability checks. */
public final class Cb6SignalUpdateCoordinator {
  public interface Completion { void success(); void failure(Exception error); }
  private static final AtomicBoolean IN_FLIGHT = new AtomicBoolean();
  private static final ExecutorService WORK = Executors.newSingleThreadExecutor();
  private static final Handler MAIN = new Handler(Looper.getMainLooper());
  private static final String TAG = "Cb6SignalUpdate";
  private Cb6SignalUpdateCoordinator() {}
  // A completion is attempted at most once. Handler rejection is observable, not silently ignored.
  private static final class Terminal {
    private final Completion callback;
    private final AtomicBoolean delivered = new AtomicBoolean();
    Terminal(Completion callback) { this.callback = callback; }
    void success() { deliver(null); }
    void failure(Exception error) { deliver(error); }
    private void deliver(Exception error) {
      if (!delivered.compareAndSet(false, true)) return;
      Runnable action = () -> {
        try { if (error == null) callback.success(); else callback.failure(error); }
        catch (RuntimeException callbackError) { Log.e(TAG, "Completion callback failed", callbackError); }
      };
      if (Looper.myLooper() == Looper.getMainLooper()) action.run();
      else if (!MAIN.post(action)) Log.e(TAG, "Main handler rejected completion");
    }
  }
  public static boolean inFlight() { return IN_FLIGHT.get(); }
  // Cleanup must not prevent completion delivery or leave the update gate locked.
  private static void finishActivation(File downloaded, SignalDatabaseActivation activation) {
    try {
      if (downloaded != null && downloaded.exists() && !downloaded.delete()) {
        Log.w(TAG, "Temporary SQLite deletion failed: " + downloaded.getName());
      }
    } catch (RuntimeException cleanupError) {
      Log.w(TAG, "Temporary SQLite cleanup exception", cleanupError);
    } finally {
      try {
        activation.shutdown();
      } catch (RuntimeException shutdownError) {
        Log.w(TAG, "Activation shutdown exception", shutdownError);
      } finally {
        IN_FLIGHT.set(false);
      }
    }
  }
  public static void start(Context context, SignalController controller, Completion callback) {
    if (Looper.myLooper() != Looper.getMainLooper()) throw new IllegalStateException("Main thread required");
    if (controller == null || callback == null) throw new IllegalArgumentException("Missing input");
    if (!IN_FLIGHT.compareAndSet(false, true)) return;
    final Terminal terminal = new Terminal(callback);
    try {
      Context app = context.getApplicationContext();
      if (app == null) throw new IllegalStateException("Application context unavailable");
      WORK.execute(() -> {
      File db = null;
      try {
        byte[] manifest = Cb6VerifiedDownloader.small(Cb6SignalDistributionConfig.MANIFEST_URL, 65536);
        byte[] signature = Cb6VerifiedDownloader.small(Cb6SignalDistributionConfig.SIGNATURE_URL, 64);
        if (signature.length != 64) throw new SecurityException("Invalid signature size");
        byte[] spki = Cb6SignalDistributionConfig.SPKI;
        byte[] prefix = {0x30,0x2a,0x30,0x05,0x06,0x03,0x2b,0x65,0x70,0x03,0x21,0x00};
        if (spki.length != 44 || !Arrays.equals(Arrays.copyOf(spki,12),prefix))
          throw new SecurityException("Invalid SPKI");
        byte[] pub = Arrays.copyOfRange(spki,12,44);
        if (!Ed25519.verify(signature,0,pub,0,manifest,0,manifest.length))
          throw new SecurityException("Signature verification failed");
        JSONObject m = new JSONObject(new String(manifest,java.nio.charset.StandardCharsets.UTF_8));
        if (!"cb6-signals-distribution-v1".equals(m.getString("format"))
            || !"signals".equals(m.getString("package_kind"))
            || !"Ed25519".equals(m.getString("signature_algorithm"))
            || !Cb6SignalDistributionConfig.KEY_ID.equals(m.getString("key_id"))
            || m.getInt("schema_version") != 2
            || !"hokkaido_signals_v2.sqlite".equals(m.getString("file"))
            || !Cb6SignalDistributionConfig.SQLITE_URL.equals(m.getString("release_asset_url")))
          throw new SecurityException("Manifest identity mismatch");
        long bytes = m.getLong("bytes");
        String sha = m.getString("sha256");
        if (bytes <= 0 || bytes > 200000000L || !sha.matches("[0-9a-f]{64}"))
          throw new SecurityException("Manifest bounds invalid");
        db = File.createTempFile("cb6-verified-", ".sqlite", app.getCacheDir());
        Cb6VerifiedDownloader.file(Cb6SignalDistributionConfig.SQLITE_URL, db, bytes);
        if (db.length() != bytes || !sha.equals(Cb6VerifiedDownloader.sha256(db)))
          throw new SecurityException("SQLite hash/length mismatch");
        File downloaded = db;
        SignalDatabaseActivation activation = new SignalDatabaseActivation(app,controller);
        try { activation.activateDownloaded(downloaded,sha,new SignalDatabaseActivation.Completion() {
          @Override public void onSuccess() {
            Exception notificationError = null;
            try { Cb6SignalDistributionConfig.onActivationCompleted(controller); }
            catch (Exception error) { notificationError = error; }
            finally { finishActivation(downloaded, activation); }
            if (notificationError != null) terminal.failure(notificationError);
            else terminal.success();
          }
          @Override public void onFailure(Exception error) {
            finishActivation(downloaded, activation);
            terminal.failure(error);
          }
        }); } catch (RuntimeException schedulingError) {
          finishActivation(downloaded, activation); throw schedulingError;
        }
      } catch (Exception error) {
        if (db != null) {
          try { if (db.exists() && !db.delete()) Log.w(TAG, "Temporary SQLite deletion failed: " + db.getName()); }
          catch (RuntimeException cleanupError) { Log.w(TAG, "Temporary SQLite cleanup exception", cleanupError); }
        }
        IN_FLIGHT.set(false);
        terminal.failure(error);
      }
    });
    } catch (RuntimeException schedulingError) {
      IN_FLIGHT.set(false);
      terminal.failure(schedulingError);
    }
  }
}
