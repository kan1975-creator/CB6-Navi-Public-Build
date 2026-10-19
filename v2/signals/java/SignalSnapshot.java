package app.organicmaps.cb6.signals;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;

/** Signal-only immutable viewport registry; never silently truncate viewport data. */
public final class SignalSnapshot
{
  public static final int MAX_VIEWPORT_POINTS=50000;
  public static final class Point
  {
    public final long id;
    public final double lat,lon;
    public final float distance;
    public Point(long id,double lat,double lon,float distance)
    {
      this.id=id; this.lat=lat; this.lon=lon; this.distance=distance;
    }
  }
  public static final SignalSnapshot EMPTY=new SignalSnapshot(Collections.emptyList());
  public final List<Point> points,topologyMembers,topologyCenters;
  public int clusteredPointCount()
  {
    HashSet<Long> centres=new HashSet<>();
    for (Point p:topologyCenters) centres.add(p.id);
    return Math.max(0,topologyMembers.size() - centres.size());
  }
  public SignalSnapshot(List<Point> candidates)
  {
    this(candidates,Collections.emptyList(),Collections.emptyList());
  }
  public SignalSnapshot(List<Point> candidates,List<Point> members,List<Point> centers)
  {
    if (candidates.size()>MAX_VIEWPORT_POINTS || members.size()>MAX_VIEWPORT_POINTS
        || centers.size()>MAX_VIEWPORT_POINTS || members.size()!=centers.size())
      throw new IllegalArgumentException("Viewport exceeds safely bounded transport");
    ArrayList<Point> sorted=new ArrayList<>();
    for (Point p:candidates)
      if (p.id>0 && SignalPolicy.validCoordinate(p.lat,p.lon) && Float.isFinite(p.distance)
          && p.distance>=0) sorted.add(p);
    sorted.sort(Comparator.comparingDouble((Point p)->p.distance).thenComparingLong(p->p.id));
    ArrayList<Point> retained=new ArrayList<>();
    HashSet<Long> seen=new HashSet<>();
    for (Point p:sorted)
      if (seen.add(p.id)) retained.add(p);
    if (retained.size()>MAX_VIEWPORT_POINTS) throw new IllegalArgumentException("Viewport overflow");
    points=Collections.unmodifiableList(retained);
    topologyMembers=Collections.unmodifiableList(new ArrayList<>(members));
    topologyCenters=Collections.unmodifiableList(new ArrayList<>(centers));
  }
  /** Keep every registered viewport point in its original coordinate. */
  public List<Point> displayPoints() { return points; }
}
