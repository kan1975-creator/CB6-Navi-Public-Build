package app.organicmaps.cb6.signals;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;

/** Signal-only immutable registry. Never contains another feature family. */
public final class SignalSnapshot
{
  public static final class Point
  {
    public final long id;
    public final double lat;
    public final double lon;
    public final float distance;

    public Point(long id, double lat, double lon, float distance)
    {
      this.id = id;
      this.lat = lat;
      this.lon = lon;
      this.distance = distance;
    }
  }

  public static final SignalSnapshot EMPTY = new SignalSnapshot(Collections.emptyList());
  public final List<Point> points;

  public SignalSnapshot(List<Point> candidates)
  {
    ArrayList<Point> sorted = new ArrayList<>();
    for (Point p : candidates)
      if (p.id > 0 && SignalPolicy.validCoordinate(p.lat, p.lon)
          && Float.isFinite(p.distance) && p.distance >= 0)
        sorted.add(p);
    sorted.sort(Comparator.comparingDouble((Point p) -> p.distance).thenComparingLong(p -> p.id));
    ArrayList<Point> retained = new ArrayList<>();
    HashSet<Long> seen = new HashSet<>();
    for (Point p : sorted)
    {
      if (seen.add(p.id)) retained.add(p);
      if (retained.size() == SignalPolicy.MAX_POINTS) break;
    }
    points = Collections.unmodifiableList(retained);
  }
}
