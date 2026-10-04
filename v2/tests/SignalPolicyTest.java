import app.organicmaps.cb6.signals.SignalPolicy;
import app.organicmaps.cb6.signals.SignalSnapshot;
import java.util.ArrayList;

public final class SignalPolicyTest
{
  private static int checks;
  private static void check(boolean value, String message)
  {
    if (!value) throw new AssertionError(message);
    ++checks;
  }
  public static void main(String[] args)
  {
    check(SignalPolicy.forward(450, 45, 0, true), "inclusive 450m/45deg");
    check(!SignalPolicy.forward(450.1f, 0, 0, true), "outside 450m");
    check(!SignalPolicy.forward(100, 45.1f, 0, true), "outside cone");
    check(SignalPolicy.forward(100, 1, 359, true), "north wrap");
    check(SignalPolicy.forward(100, -179, 179, true), "south wrap");
    check(!SignalPolicy.forward(100, 0, 0, false), "absent bearing normal");
    check(!SignalPolicy.forward(100, 0, Float.NaN, true), "invalid bearing normal");
    check(!SignalPolicy.forward(Float.NaN, 0, 0, true), "invalid distance normal");
    check(!SignalPolicy.validCoordinate(Double.NaN, 141), "invalid latitude");
    check(!SignalPolicy.validCoordinate(43, Double.POSITIVE_INFINITY), "invalid longitude");
    check(SignalPolicy.shouldRequest(0, 0, false, false, 0), "initial acquisition");
    check(!SignalPolicy.shouldRequest(11999, 0, true, true, 1000), "retry backoff despite movement");
    check(SignalPolicy.shouldRequest(12000, 0, true, true, 0), "retry at 12 seconds");
    check(!SignalPolicy.shouldRequest(44999, 0, true, false, 249), "retain before refresh");
    check(SignalPolicy.shouldRequest(45000, 0, true, false, 0), "45 second refresh");
    check(SignalPolicy.shouldRequest(12000, 0, true, false, 250), "250 metre refresh");
    ArrayList<SignalSnapshot.Point> input = new ArrayList<>();
    for (int i = 2000; i >= 1; --i) input.add(new SignalSnapshot.Point(i, 43, 141, i));
    input.add(new SignalSnapshot.Point(1, 43, 141, 1));
    input.add(new SignalSnapshot.Point(9000, Double.NaN, 141, 0));
    SignalSnapshot snapshot = new SignalSnapshot(input);
    check(snapshot.points.size() == 1400, "cap after nearest-first sort/dedup");
    check(snapshot.points.get(0).id == 1 && snapshot.points.get(1399).id == 1400, "nearest retained, not first N");
    input.clear();
    check(snapshot.points.size() == 1400, "snapshot is detached");
    ArrayList<SignalSnapshot.Point> nearbyInput = new ArrayList<>();
    nearbyInput.add(new SignalSnapshot.Point(1, 43.00000, 141.00000, 10));
    nearbyInput.add(new SignalSnapshot.Point(2, 43.00010, 141.00000, 11));
    nearbyInput.add(new SignalSnapshot.Point(3, 43.00050, 141.00000, 12));
    SignalSnapshot nearby = new SignalSnapshot(nearbyInput);
    check(nearby.displayPoints().size() == 3, "proximity alone does not merge uncertain signals");
    check(nearby.clusteredPointCount() == 0, "uncertain signals are retained without topology evidence");
    check(nearby.displayPoints().get(0).lat == nearby.points.get(0).lat
          && nearby.displayPoints().get(1).lat == nearby.points.get(1).lat
          && nearby.displayPoints().get(2).lat == nearby.points.get(2).lat,
          "proximity-only layer preserves original signal coordinates");
    ArrayList<SignalSnapshot.Point> topologyMembers = new ArrayList<>();
    ArrayList<SignalSnapshot.Point> topologyCenters = new ArrayList<>();
    topologyMembers.add(new SignalSnapshot.Point(10, 43.0, 141.0, 10));
    topologyCenters.add(new SignalSnapshot.Point(10, 43.0001, 141.0001, 11));
    SignalSnapshot topology = new SignalSnapshot(nearbyInput, topologyMembers, topologyCenters);
    check(topology.topologyMembers.size() == 1 && topology.topologyCenters.size() == 1, "confirmed topology mapping retained");
    boolean topologyMismatch = false;
    try { new SignalSnapshot(nearbyInput, topologyMembers, new ArrayList<>()); }
    catch (IllegalArgumentException e) { topologyMismatch = true; }
    check(topologyMismatch, "topology mapping mismatch rejected");
    boolean immutable = false;
    try { snapshot.points.clear(); } catch (UnsupportedOperationException e) { immutable = true; }
    check(immutable, "immutable signal registry");
    System.out.println("PASS " + checks + " signal policy/retention regression checks");
  }
}
