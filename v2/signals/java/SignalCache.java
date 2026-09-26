package app.organicmaps.cb6.signals;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

/** Versioned signal-only cache. Accessed on the signal worker, never on UI. */
final class SignalCache
{
  private final SharedPreferences preferences;
  SignalCache(Context context)
  {
    preferences = context.getSharedPreferences("cb6_v2_signals_v1", Context.MODE_PRIVATE);
  }

  SignalSnapshot read() throws Exception
  {
    JSONObject root = new JSONObject(preferences.getString("snapshot", "{}"));
    long age = System.currentTimeMillis() - root.optLong("time", 0);
    if (root.optInt("schema") != 1 || age < 0 || age > SignalPolicy.CACHE_MAX_MS)
      return SignalSnapshot.EMPTY;
    JSONArray rows = root.getJSONArray("points");
    ArrayList<SignalSnapshot.Point> points = new ArrayList<>();
    for (int i = 0; i < rows.length(); ++i)
    {
      JSONArray row = rows.getJSONArray(i);
      points.add(new SignalSnapshot.Point(row.getLong(0), row.getDouble(1), row.getDouble(2), (float) row.getDouble(3)));
    }
    return new SignalSnapshot(points);
  }

  void write(SignalSnapshot snapshot) throws Exception
  {
    JSONArray rows = new JSONArray();
    for (SignalSnapshot.Point p : snapshot.points)
      rows.put(new JSONArray().put(p.id).put(p.lat).put(p.lon).put(p.distance));
    JSONObject root = new JSONObject().put("schema", 1).put("time", System.currentTimeMillis()).put("points", rows);
    preferences.edit().putString("snapshot", root.toString()).commit();
  }
}
