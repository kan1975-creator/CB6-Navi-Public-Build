package app.organicmaps.cb6.signals;

import android.content.Context;
import android.location.Location;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import app.organicmaps.sdk.Framework;

/** Main-thread lifecycle/publisher; worker owns network/cache. No Activity references. */
public final class SignalController
{
  private final Context context;
  private final Handler main = new Handler(Looper.getMainLooper());
  private final SignalProvider provider = new CompositeSignalProvider(
      new OverpassSignalProvider(), new VerifiedSignalProvider());
  private ExecutorService worker;
  private SignalSnapshot snapshot = SignalSnapshot.EMPTY;
  private SignalSnapshot published;
  private boolean[] publishedForward;
  private Location location;
  private boolean active, renderingReady, inFlight, attempted, failed;
  private int generation;
  private long lastAttempt;
  private double lastLat, lastLon;

  public SignalController(Context context) { this.context = context.getApplicationContext(); }

  public void start(boolean ready)
  {
    if (active) return;
    active = true;
    renderingReady = ready;
    published = null;
    publishedForward = null;
    attempted = false;
    int token = ++generation;
    worker = Executors.newSingleThreadExecutor();
    worker.execute(() -> {
      try
      {
        SignalSnapshot cached = new SignalCache(context).read();
        main.post(() -> {
          if (!active || token != generation || !snapshot.points.isEmpty()) return;
          snapshot = cached;
          publish();
        });
      }
      catch (Exception ignored) { /* Optional cache never blocks CoMaps startup. */ }
    });
    main.post(tick);
    publish();
  }

  public void stop()
  {
    active = false;
    renderingReady = false;
    ++generation;
    main.removeCallbacks(tick);
    if (worker != null) worker.shutdownNow();
    worker = null;
    inFlight = false;
    location = null;
  }

  public void renderingReady()
  {
    renderingReady = true;
    published = null;
    publishedForward = null;
    publish();
    requestIfNeeded();
  }

  public void onLocation(Location update)
  {
    if (!active || !SignalPolicy.validCoordinate(update.getLatitude(), update.getLongitude())) return;
    location = new Location(update); // hasBearing belongs to THIS fix, never a stale retained heading.
    Framework.nativeLogCb6MwmSignals(location.getLatitude(), location.getLongitude());
    publish();
    requestIfNeeded();
  }

  private final Runnable tick = new Runnable()
  {
    @Override public void run()
    {
      if (!active) return;
      requestIfNeeded();
      main.postDelayed(this, 1000);
    }
  };

  private void requestIfNeeded()
  {
    if (!active || inFlight || location == null) return;
    long now = SystemClock.elapsedRealtime();
    float[] distance = new float[1];
    if (attempted) Location.distanceBetween(lastLat, lastLon, location.getLatitude(), location.getLongitude(), distance);
    if (!SignalPolicy.shouldRequest(now, lastAttempt, attempted, failed, distance[0])) return;
    lastLat = location.getLatitude();
    lastLon = location.getLongitude();
    lastAttempt = now;
    attempted = true;
    inFlight = true;
    final double lat = lastLat, lon = lastLon;
    final int token = generation;
    worker.execute(() -> {
      SignalSnapshot result = null;
      try { result = provider.load(lat, lon); }
      catch (Exception ignored) { /* Last valid snapshot remains visible. */ }
      final SignalSnapshot loaded = result;
      main.post(() -> {
        if (!active || token != generation) return;
        inFlight = false;
        failed = loaded == null;
        if (failed) lastAttempt = SystemClock.elapsedRealtime(); // retry 12s after failure, no busy loop
        else
        {
          snapshot = loaded;
          publish();
        }
        Log.i("CB6-SIGNAL-DIAG", failed ? "refresh-failed retained=" + snapshot.points.size()
            : "refresh-loaded=" + loaded.points.size());
        if (app.organicmaps.BuildConfig.DEBUG)
          Log.i("CB6-V2-Signal", failed ? "refresh failed; retained snapshot" : "loaded=" + loaded.points.size());
      });
      if (result != null && !Thread.currentThread().isInterrupted())
        try { new SignalCache(context).write(result); } catch (Exception ignored) { }
    });
  }

  private void publish()
  {
    Log.i("CB6-SIGNAL-DIAG", "publish-enter active=" + active + " ready=" + renderingReady
        + " acquired=" + snapshot.points.size() + " location=" + (location != null));
    if (!active || !renderingReady || location == null) return;
    java.util.List<SignalSnapshot.Point> display = snapshot.displayPoints();
    if (app.organicmaps.BuildConfig.DEBUG)
      Log.i("CB6-V2-Signal", "publish acquired=" + snapshot.points.size()
          + " display=" + display.size() + " clustered=" + snapshot.clusteredPointCount());
    int n = display.size();
    long[] ids = new long[n];
    double[] lats = new double[n], lons = new double[n];
    boolean[] forward = new boolean[n];
    float[] result = new float[3];
    for (int i = 0; i < n; ++i)
    {
      SignalSnapshot.Point p = display.get(i);
      ids[i] = p.id;
      lats[i] = p.lat;
      lons[i] = p.lon;
      if (location != null && location.hasBearing())
      {
        Location.distanceBetween(location.getLatitude(), location.getLongitude(), p.lat, p.lon, result);
        forward[i] = SignalPolicy.forward(result[0], result[1], location.getBearing(), true);
      }
    }
    if (location != null)
    {
      float[] diagnosticDistance = new float[1];
      for (SignalSnapshot.Point p : display)
      {
        Location.distanceBetween(location.getLatitude(), location.getLongitude(),
            p.lat, p.lon, diagnosticDistance);
        if (diagnosticDistance[0] <= 1000.0f)
          Log.i("CB6-SIGNAL-DIAG", "point id=" + p.id + " lat=" + p.lat + " lon=" + p.lon
              + " distance=" + diagnosticDistance[0]);
      }
    }
    if (published == snapshot && Arrays.equals(publishedForward, forward))
    {
      Log.i("CB6-SIGNAL-DIAG", "publish-skip unchanged display=" + n);
      return;
    }
    Log.i("CB6-SIGNAL-DIAG", "jni-send acquired=" + snapshot.points.size()
        + " display=" + n + " clustered=" + snapshot.clusteredPointCount());
    int t = snapshot.topologyMembers.size();
    double[] memberLats = new double[t], memberLons = new double[t], centerLats = new double[t], centerLons = new double[t];
    for (int i = 0; i < t; ++i)
    {
      SignalSnapshot.Point member = snapshot.topologyMembers.get(i), center = snapshot.topologyCenters.get(i);
      memberLats[i] = member.lat; memberLons[i] = member.lon;
      centerLats[i] = center.lat; centerLons[i] = center.lon;
    }
    Framework.nativeSetCb6Signals(location.getLatitude(), location.getLongitude(), ids, lats, lons, forward,
        memberLats, memberLons, centerLats, centerLons);
    published = snapshot;
    publishedForward = forward;
  }
}
