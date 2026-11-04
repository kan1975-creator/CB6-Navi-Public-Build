package app.organicmaps.cb6.signals;

import android.os.Looper;
import android.util.Base64;
/** Trusted release identity and main-thread-only controller handoff. */
public final class Cb6SignalDistributionConfig {
  private Cb6SignalDistributionConfig() {}
  public static final String KEY_ID = "c966161b7b959177";
  public static final String RELEASE = "https://github.com/kan1975-creator/CB6-Navi-Public-Build/releases/download/cb6-signals-v2-20261105/";
  public static final String MANIFEST_URL = RELEASE + "cb6_signals_manifest.json";
  public static final String SIGNATURE_URL = RELEASE + "cb6_signals_manifest.sig";
  public static final String SQLITE_URL = RELEASE + "hokkaido_signals_v2.sqlite";
  public static final byte[] SPKI = Base64.decode("MCowBQYDK2VwAyEAQt8eqWbD+oQ6Raf0ZzenvXC1qJdRY11rsJA6NjCfMsE=", Base64.DEFAULT);
  private static SignalController controller;
  private static boolean pendingActivation;
  private static boolean started;
  private static void mainOnly() {
    if (Looper.myLooper() != Looper.getMainLooper()) throw new IllegalStateException("Main thread required");
  }
  public static void register(SignalController value) {
    mainOnly(); if (value == null) throw new IllegalArgumentException("controller"); controller = value; started = false;
  }
  public static void unregister(SignalController value) {
    mainOnly(); if (controller == value) { controller = null; started = false; }
  }
  public static SignalController current() { mainOnly(); return controller; }
  /** Called immediately before stopping this controller. */
  public static void onControllerStopping(SignalController value) {
    mainOnly();
    if (controller == value) started = false;
  }
  /** Existing activation already notified its original controller before completion. */
  public static void onActivationCompleted(SignalController original) {
    mainOnly();
    // The existing activation owns notification of the original controller.
    // Only a replacement controller needs an additional notification.
    if (controller == original && started) { pendingActivation = false; return; }
    pendingActivation = true;
    if (controller != null && started) deliverPending(controller);
  }
  /** Called only after the current controller has been started on the main thread. */
  public static void onControllerStarted(SignalController value) {
    mainOnly();
    if (value == null || controller != value) return;
    started = true;
    deliverPending(value);
  }
  private static void deliverPending(SignalController value) {
    mainOnly();
    if (!pendingActivation || !started || controller != value) return;
    // Consume before invoking to prevent duplicate notification after a partial side effect.
    // An exception may now lose the notification; durable exactly-once requires an ack API.
    pendingActivation = false;
    value.onSignalDatabaseActivated();
  }
}
