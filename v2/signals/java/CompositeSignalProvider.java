package app.organicmaps.cb6.signals;

import android.location.Location;
import java.util.ArrayList;
import java.util.List;

/** Merges primary OSM acquisition with independently verified supplemental signal records. */
public final class CompositeSignalProvider implements SignalProvider
{
  private final SignalProvider primary;
  private final SignalProvider supplement;

  public CompositeSignalProvider(SignalProvider primary, SignalProvider supplement)
  {
    this.primary = primary;
    this.supplement = supplement;
  }

  @Override
  public SignalSnapshot load(double lat, double lon) throws Exception
  {
    SignalSnapshot a = null, b = null;
    Exception primaryError = null, supplementError = null;
    try { a = primary.load(lat, lon); } catch (Exception e) { primaryError = e; }
    try { b = supplement.load(lat, lon); } catch (Exception e) { supplementError = e; }
    // A supplemental provider with zero records must not mask primary acquisition failure.
    // Propagate failure so SignalController keeps the previous marks and uses its retry path.
    if (primaryError != null && (b == null || b.points.isEmpty()))
      throw new IllegalStateException("Primary signal provider unavailable and supplement empty", primaryError);
    if (a == null && b == null)
      throw new IllegalStateException("All signal providers unavailable",
          supplementError);

    ArrayList<SignalSnapshot.Point> merged = new ArrayList<>();
    ArrayList<SignalSnapshot.Point> topologyMembers = new ArrayList<>();
    ArrayList<SignalSnapshot.Point> topologyCenters = new ArrayList<>();
    if (a != null)
    {
      merged.addAll(a.points);
      topologyMembers.addAll(a.topologyMembers);
      topologyCenters.addAll(a.topologyCenters);
    }
    if (b != null)
      for (SignalSnapshot.Point candidate : b.points)
        if (!nearAny(candidate, merged)) merged.add(candidate);
    return new SignalSnapshot(merged, topologyMembers, topologyCenters);
  }

  private static boolean nearAny(SignalSnapshot.Point candidate, List<SignalSnapshot.Point> points)
  {
    float[] distance = new float[1];
    for (SignalSnapshot.Point existing : points)
    {
      Location.distanceBetween(candidate.lat, candidate.lon, existing.lat, existing.lon, distance);
      if (distance[0] <= SignalPolicy.SOURCE_DEDUP_M) return true;
    }
    return false;
  }
}
