package app.organicmaps.cb6.signals;

import android.location.Location;
import java.util.ArrayList;

/**
 * Verified supplemental signal dataset boundary.
 * Records must be reviewed data with provenance; never infer coordinates from screenshots.
 */
public final class VerifiedSignalProvider implements SignalProvider
{
  private static final long ID_NAMESPACE = (1L << 61);
  private static final Record[] RECORDS = {
      // Intentionally empty until an exact coordinate + provenance + verification date are reviewed.
  };

  static final class Record
  {
    final long id;
    final double lat, lon;
    final String provenance, verifiedDate;
    Record(long id, double lat, double lon, String provenance, String verifiedDate)
    {
      this.id = id; this.lat = lat; this.lon = lon;
      this.provenance = provenance; this.verifiedDate = verifiedDate;
    }
  }

  @Override
  public SignalSnapshot load(double lat, double lon)
  {
    ArrayList<SignalSnapshot.Point> points = new ArrayList<>();
    float[] distance = new float[1];
    for (Record record : RECORDS)
    {
      if (!SignalPolicy.validCoordinate(record.lat, record.lon)
          || record.id <= 0 || record.id >= (1L << 61)
          || record.provenance == null || record.provenance.trim().isEmpty()
          || record.verifiedDate == null || !record.verifiedDate.matches("\\d{4}-\\d{2}-\\d{2}"))
        throw new IllegalStateException("Invalid verified signal record");
      Location.distanceBetween(lat, lon, record.lat, record.lon, distance);
      if (distance[0] <= SignalPolicy.RADIUS_M)
        points.add(new SignalSnapshot.Point(ID_NAMESPACE | record.id, record.lat, record.lon, distance[0]));
    }
    return new SignalSnapshot(points);
  }
}
