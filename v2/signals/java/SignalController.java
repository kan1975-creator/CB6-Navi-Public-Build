package app.organicmaps.cb6.signals;

import android.content.Context;
import android.location.Location;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import java.io.InputStream;
import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import app.organicmaps.sdk.Framework;

/** Main-thread lifecycle and publisher; worker owns only local signed SQLite. */
public final class SignalController
{
  public interface UpdateCallback { void onFinished(String status); }
  private final Context context;
  private final Handler main = new Handler(Looper.getMainLooper());
  private final OfflineSignalProvider provider;
  private ExecutorService worker;
  private SignalSnapshot snapshot = SignalSnapshot.EMPTY;
  private SignalSnapshot published;
  private boolean[] publishedForward;
  private Location location;
  private boolean active, renderingReady, inFlight;
  private int generation;
  private double[] queriedBounds;
  private long viewportToken;

  public SignalController(Context context)
  {
    this.context = context.getApplicationContext();
    provider = new OfflineSignalProvider(this.context);
  }

  public void start(boolean ready)
  {
    if (active) return;
    active = true;
    renderingReady = ready;
    published = null;
    publishedForward = null;
    queriedBounds = null;
    int token = ++generation;
    worker = Executors.newSingleThreadExecutor();
    worker.execute(() -> {
      try { provider.bootstrapIfNeeded(); }
      catch (Exception ex) { Log.w("CB6-OFFLINE", "bootstrap-unavailable: " + ex.getClass().getSimpleName()); }
      main.post(() -> {
        if (!active || token != generation) return;
        requestIfNeeded();
      });
    });
    main.post(tick);
    publish();
  }

  public void stop()
  {
    active = false;
    renderingReady = false;
    ++generation;
    ++viewportToken;
    main.removeCallbacks(tick);
    if (worker != null) worker.shutdownNow();
    worker = null;
    inFlight = false;
    queriedBounds = null;
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
    if (!active || !SignalPolicy.validCoordinate(update.getLatitude(),update.getLongitude())) return;
    location = new Location(update);
    publishedForward = null;  // A new fix can change heading emphasis.
    publish();
  }

  private double[] visibleBounds()
  {
    if (!active || !renderingReady) return null;
    double[] b = Framework.nativeGetCb6SignalViewportBounds();
    if (b==null || b.length!=4 || !SignalPolicy.validCoordinate(b[0],b[1])
        || !SignalPolicy.validCoordinate(b[2],b[3]) || b[0]>b[2] || b[1]>b[3])
      return null;
    return b;
  }

  private final Runnable tick = new Runnable()
  {
    @Override public void run()
    {
      if (!active) return;
      requestIfNeeded();
      main.postDelayed(this,500);
    }
  };

  private void requestIfNeeded()
  {
    if (!active || inFlight || worker==null) return;
    double[] bounds=visibleBounds();
    if (bounds==null || Arrays.equals(bounds,queriedBounds)) return;
    queriedBounds=bounds.clone();
    // Never leave stale previous-viewport OSM marks on the newly visible map.
    // MWM original anchors remain available even when an offline DB is absent.
    snapshot=SignalSnapshot.EMPTY;
    published=null;
    publish();
    final int token=generation;
    final long viewport=++viewportToken;
    inFlight=true;
    worker.execute(() -> {
      SignalSnapshot next=null;
      try { next=provider.loadViewport(bounds[0],bounds[1],bounds[2],bounds[3]); }
      catch (Exception error) { Log.w("CB6-OFFLINE", "read-failed: "+error.getClass().getSimpleName()); }
      SignalSnapshot result=next;
      main.post(() -> {
        if (!active || generation!=token) return;
        inFlight=false;
        double[] current=visibleBounds();
        // Never publish a completed query for a viewport which has since moved.
        if (viewport!=viewportToken || !Arrays.equals(bounds,current))
        {
          requestIfNeeded();
          return;
        }
        if (result!=null)
        {
          snapshot=result;
          publish();
        }
        // Failure retains the last valid snapshot, and does not request network.
        // A future viewport change or explicit signed import permits another read.
      });
    });
  }

  /** Activity invokes this only after explicit system document selection. */
  public void importSignedZip(Uri uri, UpdateCallback onDone)
  {
    if (uri==null || worker==null || !active) return;
    int token=generation;
    worker.execute(() -> {
      String message;
      try (InputStream in=context.getContentResolver().openInputStream(uri))
      {
        if (in==null) throw new java.io.IOException("No document stream");
        int version=provider.importOwnerSignedZip(in);
        message="CB6 北海道信号機データ更新完了: " + version;
      }
      catch (Exception error)
      {
        message="CB6 更新拒否・旧DB維持: " + error.getClass().getSimpleName();
      }
      final String status=message;
      main.post(() -> {
        if (!active || token!=generation) return;
        queriedBounds=null;
        published=null;
        requestIfNeeded();
        onDone.onFinished(status);
      });
    });
  }

  private void publish()
  {
    double[] b=visibleBounds();
    if (!active || !renderingReady || b==null) return;
    java.util.List<SignalSnapshot.Point> display=snapshot.displayPoints();
    int n=display.size();
    long[] ids=new long[n];
    double[] lats=new double[n],lons=new double[n];
    boolean[] forward=new boolean[n];
    float[] dist=new float[3];
    for (int i=0;i<n;i++)
    {
      SignalSnapshot.Point p=display.get(i);
      ids[i]=p.id; lats[i]=p.lat; lons[i]=p.lon;
      if (location!=null && location.hasBearing())
      {
        Location.distanceBetween(location.getLatitude(),location.getLongitude(),p.lat,p.lon,dist);
        forward[i]=SignalPolicy.forward(dist[0],dist[1],location.getBearing(),true);
      }
    }
    if (published==snapshot && Arrays.equals(publishedForward,forward)) return;
    int t=snapshot.topologyMembers.size();
    double[] memberLats=new double[t],memberLons=new double[t];
    double[] centerLats=new double[t],centerLons=new double[t];
    long[] memberIds=new long[t],centerIds=new long[t];
    for (int i=0;i<t;i++)
    {
      SignalSnapshot.Point member=snapshot.topologyMembers.get(i), center=snapshot.topologyCenters.get(i);
      memberLats[i]=member.lat; memberLons[i]=member.lon;
      centerLats[i]=center.lat; centerLons[i]=center.lon;
      memberIds[i] = member.id; centerIds[i] = center.id;
    }
    // 12 existing JNI Java arguments retain the exact type and order.
    Framework.nativeSetCb6Signals((b[0]+b[2])/2.0,(b[1]+b[3])/2.0,
      ids,lats,lons,forward,memberLats,memberLons,centerLats,centerLons,memberIds,centerIds);
    published=snapshot;
    publishedForward=forward;
  }
}
