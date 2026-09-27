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

  /** Renderer-only clustering. Acquired OSM points/cache remain untouched. */
  public List<Point> displayPoints()
  {
    final class Group
    {
      final Point anchor;
      long minId;
      double latSum, lonSum;
      int count;
      float minDistance;
      Group(Point p)
      {
        anchor = p; minId = p.id; latSum = p.lat; lonSum = p.lon; count = 1; minDistance = p.distance;
      }
      void add(Point p)
      {
        minId = Math.min(minId, p.id);
        latSum += p.lat; lonSum += p.lon; ++count;
        minDistance = Math.min(minDistance, p.distance);
      }
      Point centre() { return new Point(minId, latSum / count, lonSum / count, minDistance); }
    }

    ArrayList<Group> groups = new ArrayList<>();
    for (Point candidate : points)
    {
      Group match = null;
      for (Group group : groups)
      {
        // Compare to the immutable first-node anchor: prevents transitive chaining into the next junction.
        if (metres(candidate.lat, candidate.lon, group.anchor.lat, group.anchor.lon)
            <= SignalPolicy.DISPLAY_CLUSTER_M)
        {
          match = group;
          break;
        }
      }
      if (match == null) groups.add(new Group(candidate));
      else match.add(candidate);
    }
    ArrayList<Point> visible = new ArrayList<>();
    for (Group group : groups) visible.add(group.centre());
    return Collections.unmodifiableList(visible);
  }

  private static double metres(double lat1, double lon1, double lat2, double lon2)
  {
    double p1 = Math.toRadians(lat1), p2 = Math.toRadians(lat2);
    double dp = Math.toRadians(lat2 - lat1), dl = Math.toRadians(lon2 - lon1);
    double a = Math.sin(dp / 2) * Math.sin(dp / 2)
        + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return 6371000.0 * 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
  }
}
