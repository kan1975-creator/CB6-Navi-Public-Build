package app.organicmaps.cb6.signals;

import android.content.Context;
import android.location.Location;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Build-time road graph membership. No graph traversal or network at runtime. */
final class GraphSignalTopology {
  private static volatile Map<Long, Entry> cached;
  private static final class Entry {
    final long member, center;
    final double lat, lon, centerLat, centerLon;
    Entry(String[] row) {
      member=Long.parseLong(row[0]); center=Long.parseLong(row[1]);
      lat=Double.parseDouble(row[2]); lon=Double.parseDouble(row[3]);
      centerLat=Double.parseDouble(row[4]); centerLon=Double.parseDouble(row[5]);
      if (member<=0 || center<=0 || !SignalPolicy.validCoordinate(lat,lon)
          || !SignalPolicy.validCoordinate(centerLat,centerLon))
        throw new IllegalArgumentException("Invalid graph topology row");
    }
  }
  private static Map<Long, Entry> entries(Context context) throws Exception {
    Map<Long, Entry> result=cached;
    if (result!=null) return result;
    synchronized(GraphSignalTopology.class) {
      if (cached!=null) return cached;
      HashMap<Long, Entry> rows=new HashMap<>();
      try (BufferedReader reader=new BufferedReader(new InputStreamReader(
          context.getAssets().open("cb6_graph_topology.csv"),StandardCharsets.UTF_8))) {
        if (!"member_id,center_id,member_lat,member_lon,center_lat,center_lon".equals(reader.readLine()))
          throw new IllegalStateException("Invalid graph topology header");
        String line;
        while((line=reader.readLine())!=null) {
          String[] fields=line.split(",",-1);
          if (fields.length!=6) throw new IllegalStateException("Invalid graph topology columns");
          Entry e=new Entry(fields);
          if (rows.put(e.member,e)!=null) throw new IllegalStateException("Duplicate graph member");
        }
      }
      for (Entry e:rows.values()) {
        Entry root=rows.get(e.center);
        if (root==null || root.center!=e.center || root.centerLat!=e.centerLat || root.centerLon!=e.centerLon)
          throw new IllegalStateException("Invalid graph topology root");
      }
      cached=Collections.unmodifiableMap(rows);
      return cached;
    }
  }
  static void apply(Context context,List<SignalSnapshot.Point> points,
      ArrayList<SignalSnapshot.Point> members,ArrayList<SignalSnapshot.Point> centers) throws Exception {
    Map<Long, Entry> rows=entries(context);
    // Retire legacy distance topology. An unresolved ID stays independent.
    members.clear(); centers.clear();
    float[] distance=new float[1];
    for (SignalSnapshot.Point point:points) {
      Entry e=rows.get(point.id);
      if (e==null) continue;
      Location.distanceBetween(point.lat,point.lon,e.lat,e.lon,distance);
      // IDs are exact OSM node IDs; stale coordinates never acquire a new group.
      if (distance[0]>0.5f) continue;
      members.add(point);
      centers.add(new SignalSnapshot.Point(e.center,e.centerLat,e.centerLon,point.distance));
    }
  }
}
