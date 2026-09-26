package app.organicmaps.cb6.signals;

import android.location.Location;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/** Frozen lightweight signal-only acquisition; never queries static POIs. */
public final class OverpassSignalProvider implements SignalProvider
{
  private static final String[] ENDPOINTS = {
      "https://overpass-api.de/api/interpreter",
      "https://overpass.kumi.systems/api/interpreter",
      "https://overpass.nchc.org.tw/api/interpreter"
  };

  @Override
  public SignalSnapshot load(double lat, double lon) throws Exception
  {
    String ll = String.format(Locale.US, "%.6f,%.6f", lat, lon);
    String query = "[out:json][timeout:8];("
        + "node(around:" + SignalPolicy.RADIUS_M + "," + ll + ")[highway=traffic_signals];"
        + "node(around:" + SignalPolicy.RADIUS_M + "," + ll + ")[crossing=traffic_signals];"
        + ");out body;";
    Exception last = null;
    for (String endpoint : ENDPOINTS)
    {
      if (Thread.currentThread().isInterrupted()) throw new InterruptedException();
      try
      {
        SignalSnapshot snapshot = parse(new JSONObject(post(endpoint, query)), lat, lon);
        // Match accepted retention: empty/failed endpoint never erases valid marks.
        if (!snapshot.points.isEmpty()) return snapshot;
        last = new IllegalStateException("Empty signal response");
      }
      catch (Exception error) { last = error; }
    }
    throw new IllegalStateException("Signal providers unavailable", last);
  }

  static SignalSnapshot parse(JSONObject root, double lat, double lon) throws Exception
  {
    // Overpass may return HTTP 200 with a timeout/runtime error and partial data.
    if (root.has("remark")) throw new IllegalStateException("Incomplete Overpass response");
    JSONArray elements = root.getJSONArray("elements");
    ArrayList<SignalSnapshot.Point> points = new ArrayList<>();
    float[] distance = new float[1];
    for (int i = 0; i < elements.length(); ++i)
    {
      JSONObject e = elements.optJSONObject(i);
      if (e == null || !"node".equals(e.optString("type"))) continue;
      JSONObject tags = e.optJSONObject("tags");
      if (tags == null) continue;
      boolean roadSignal = "traffic_signals".equals(tags.optString("highway"));
      boolean crossingSignal = "traffic_signals".equals(tags.optString("crossing"));
      if (!roadSignal && !crossingSignal) continue;
      double y = e.optDouble("lat", Double.NaN), x = e.optDouble("lon", Double.NaN);
      if (!SignalPolicy.validCoordinate(y, x)) continue;
      Location.distanceBetween(lat, lon, y, x, distance);
      points.add(new SignalSnapshot.Point(e.optLong("id", -1), y, x, distance[0]));
    }
    return new SignalSnapshot(points); // Sort ALL candidates before the 1400 cap.
  }

  private static String post(String endpoint, String query) throws Exception
  {
    HttpURLConnection connection = (HttpURLConnection) new URL(endpoint).openConnection();
    try
    {
      connection.setConnectTimeout(4000);
      connection.setReadTimeout(8000);
      connection.setRequestMethod("POST");
      connection.setDoOutput(true);
      connection.setRequestProperty("User-Agent", "CB6-Navi/V2-Signals CoMaps-supplement");
      connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
      byte[] body = ("data=" + URLEncoder.encode(query, StandardCharsets.UTF_8.name()))
          .getBytes(StandardCharsets.UTF_8);
      try (OutputStream stream = connection.getOutputStream()) { stream.write(body); }
      int status = connection.getResponseCode();
      if (status < 200 || status >= 300) throw new IllegalStateException("HTTP " + status);
      try (InputStream stream = connection.getInputStream(); ByteArrayOutputStream bytes = new ByteArrayOutputStream())
      {
        byte[] buffer = new byte[8192];
        int n;
        while ((n = stream.read(buffer)) != -1)
        {
          if (Thread.currentThread().isInterrupted()) throw new InterruptedException();
          if (bytes.size() + n > 8 * 1024 * 1024) throw new IllegalStateException("Signal response too large");
          bytes.write(buffer, 0, n);
        }
        return bytes.toString(StandardCharsets.UTF_8.name());
      }
    }
    finally { connection.disconnect(); }
  }
}
