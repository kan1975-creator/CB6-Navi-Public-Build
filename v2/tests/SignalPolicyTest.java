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
    boolean immutable = false;
    try { snapshot.points.clear(); } catch (UnsupportedOperationException e) { immutable = true; }
    check(immutable, "immutable signal registry");
    System.out.println("PASS " + checks + " signal policy/retention regression checks");
  }
}
