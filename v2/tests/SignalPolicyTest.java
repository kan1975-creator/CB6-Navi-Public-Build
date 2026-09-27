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
    ArrayList<SignalSnapshot.Point> clusterInput = new ArrayList<>();
    clusterInput.add(new SignalSnapshot.Point(1, 43.00000, 141.00000, 10));
    clusterInput.add(new SignalSnapshot.Point(2, 43.00010, 141.00000, 11)); // about 11 m: same visual intersection group
    clusterInput.add(new SignalSnapshot.Point(3, 43.00050, 141.00000, 12)); // about 56 m: separate signal remains
    SignalSnapshot clustered = new SignalSnapshot(clusterInput);
    check(clustered.points.size() == 3, "clustering never deletes acquired signal data");
    check(clustered.displayPoints().size() == 2, "nearby intersection signals collapse only for display");
    check(clustered.clusteredPointCount() == 1, "diagnostic exposes renderer-only clustered count");
    check(clustered.displayPoints().get(0).id == 1 && clustered.displayPoints().get(1).id == 3,
          "deterministic group id retained and separate signal preserved");
    check(Math.abs(clustered.displayPoints().get(0).lat - 43.00005) < 0.000001,
          "cluster icon is centred between physical signal nodes");
    ArrayList<SignalSnapshot.Point> chainInput = new ArrayList<>();
    chainInput.add(new SignalSnapshot.Point(11, 43.00000, 141.00000, 10));
    chainInput.add(new SignalSnapshot.Point(12, 43.00020, 141.00000, 11)); // ~22m from anchor
    chainInput.add(new SignalSnapshot.Point(13, 43.00040, 141.00000, 12)); // ~44m from anchor, ~22m from member
    check(new SignalSnapshot(chainInput).displayPoints().size() == 2,
          "display clustering cannot chain adjacent junctions together");
    boolean immutable = false;
    try { snapshot.points.clear(); } catch (UnsupportedOperationException e) { immutable = true; }
    check(immutable, "immutable signal registry");
    System.out.println("PASS " + checks + " signal policy/retention regression checks");
  }
}
