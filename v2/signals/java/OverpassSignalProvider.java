package app.organicmaps.cb6.signals;

import android.location.Location;
import android.util.Log;
import app.organicmaps.sdk.Framework;
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
  // OSM node, way and relation ids use separate positive namespaces.
  private static final long WAY_ID_NAMESPACE = 1L << 62;
  private static final long RELATION_ID_NAMESPACE = (1L << 62) | (1L << 61);
  private static final long RELATION_RAW_ID_LIMIT = 1L << 61;
  private static final int TOPOLOGY_BATCH_SIZE = 64;
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
        + "way(around:" + SignalPolicy.RADIUS_M + "," + ll + ")[crossing=traffic_signals];"
        + "rel(around:" + SignalPolicy.RADIUS_M + "," + ll + ")[type=traffic_signals_set];"
        + ");out center geom;";
    Exception last = null;
    for (int endpointIndex = 0; endpointIndex < ENDPOINTS.length; ++endpointIndex)
    {
      String endpoint = ENDPOINTS[endpointIndex];
      if (Thread.currentThread().isInterrupted()) throw new InterruptedException();
      try
      {
        SignalSnapshot snapshot = parse(new JSONObject(post(endpoint, query)), lat, lon);
        // Match accepted retention: empty/failed endpoint never erases valid marks.
        if (!snapshot.points.isEmpty())
        {
          Log.i("CB6-SIGNAL-DIAG", "provider-endpoint=" + endpointIndex
              + " result=points count=" + snapshot.points.size());
          logMwmDirectDuplicateCandidates(snapshot, lat, lon);
          return applySignalNodeCenterClusters(endpoint, snapshot, lat, lon);
        }
        Log.i("CB6-SIGNAL-DIAG", "provider-endpoint=" + endpointIndex + " result=empty");
        last = new IllegalStateException("Empty signal response");
      }
      catch (Exception error)
      {
        Log.i("CB6-SIGNAL-DIAG", "provider-endpoint=" + endpointIndex
            + " result=error type=" + error.getClass().getSimpleName());
        last = error;
      }
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
      if (e == null) continue;
      String type = e.optString("type");
      if (!"node".equals(type) && !"way".equals(type) && !"relation".equals(type)) continue;
      JSONObject tags = e.optJSONObject("tags");
      if (tags == null) continue;
      boolean roadSignal = "traffic_signals".equals(tags.optString("highway"));
      boolean crossingSignal = "traffic_signals".equals(tags.optString("crossing"));
      boolean signalSet = "traffic_signals_set".equals(tags.optString("type"));
      if (!roadSignal && !crossingSignal && !signalSet) continue;
      if (signalSet && "relation".equals(type))
        logSignalSetMembers(e);
      double y, x;
      if ("node".equals(type))
      {
        y = e.optDouble("lat", Double.NaN);
        x = e.optDouble("lon", Double.NaN);
      }
      else
      {
        JSONObject center = e.optJSONObject("center");
        if (center == null) continue;
        y = center.optDouble("lat", Double.NaN);
        x = center.optDouble("lon", Double.NaN);
      }
      if (!SignalPolicy.validCoordinate(y, x)) continue;
      long rawId = e.optLong("id", -1);
      if (rawId <= 0) continue;
      long id;
      if ("relation".equals(type))
      {
        if (rawId >= RELATION_RAW_ID_LIMIT) continue;
        id = RELATION_ID_NAMESPACE | rawId;
      }
      else
      {
        if (rawId >= WAY_ID_NAMESPACE) continue;
        id = "way".equals(type) ? WAY_ID_NAMESPACE | rawId : rawId;
      }
      Location.distanceBetween(lat, lon, y, x, distance);
      points.add(new SignalSnapshot.Point(id, y, x, distance[0]));
    }
    return new SignalSnapshot(points); // Sort ALL candidates before the 1400 cap.
  }

  private static void logMwmDirectDuplicateCandidates(
      SignalSnapshot snapshot, double originLat, double originLon)
  {
    ArrayList<SignalSnapshot.Point> nodes = new ArrayList<>();
    for (SignalSnapshot.Point point : snapshot.points)
      if (point.id > 0 && point.id < WAY_ID_NAMESPACE) nodes.add(point);
    long[] ids = new long[nodes.size()];
    double[] lats = new double[nodes.size()];
    double[] lons = new double[nodes.size()];
    for (int i = 0; i < nodes.size(); ++i)
    {
      SignalSnapshot.Point point = nodes.get(i);
      ids[i] = point.id;
      lats[i] = point.lat;
      lons[i] = point.lon;
    }
    Framework.nativeLogCb6MwmDirectDuplicateCandidates(originLat, originLon, ids, lats, lons);
  }

  private static void logSignalSetMembers(JSONObject relation)
  {
    long relationId = relation.optLong("id", -1);
    JSONArray members = relation.optJSONArray("members");
    if (relationId <= 0 || members == null) return;
    for (int i = 0; i < members.length(); ++i)
    {
      JSONObject member = members.optJSONObject(i);
      if (member == null) continue;
      long memberId = member.optLong("ref", -1);
      String role = member.optString("role");
      double lat = member.optDouble("lat", Double.NaN);
      double lon = member.optDouble("lon", Double.NaN);
      if ((!Double.isFinite(lat) || !Double.isFinite(lon)) && member.has("geometry"))
      {
        JSONArray geometry = member.optJSONArray("geometry");
        if (geometry != null && geometry.length() > 0)
        {
          JSONObject first = geometry.optJSONObject(0);
          JSONObject last = geometry.optJSONObject(geometry.length() - 1);
          if (first != null && last != null)
          {
            double firstLat = first.optDouble("lat", Double.NaN);
            double firstLon = first.optDouble("lon", Double.NaN);
            double lastLat = last.optDouble("lat", Double.NaN);
            double lastLon = last.optDouble("lon", Double.NaN);
            if (SignalPolicy.validCoordinate(firstLat, firstLon)
                && SignalPolicy.validCoordinate(lastLat, lastLon))
            {
              lat = (firstLat + lastLat) / 2.0;
              lon = (firstLon + lastLon) / 2.0;
            }
          }
        }
      }
      Log.i("CB6-SIGNAL-SET-DIAG", "relation=" + relationId
          + " member=" + memberId + " role=" + role
          + " lat=" + lat + " lon=" + lon);
    }
  }

  private static SignalSnapshot applySignalNodeCenterClusters(
      String endpoint, SignalSnapshot snapshot, double originLat, double originLon)
  {
    ArrayList<SignalSnapshot.Point> diagnosticPoints = new ArrayList<>();
    ArrayList<Long> nodeIds = new ArrayList<>();
    for (SignalSnapshot.Point point : snapshot.points)
    {
      // Way/relation ids are namespaced above the raw OSM node-id range.
      if (point.id >= WAY_ID_NAMESPACE) continue;
      diagnosticPoints.add(point);
      nodeIds.add(point.id);
      Log.i("CB6-SIGNAL-WAY-DIAG", "node=" + point.id
          + " lat=" + point.lat + " lon=" + point.lon + " distance=" + point.distance);
    }
    if (nodeIds.isEmpty())
    {
      Log.i("CB6-SIGNAL-WAY-DIAG", "stage=complete result=zero-node-ids");
      return snapshot;
    }
    if (nodeIds.size() > TOPOLOGY_BATCH_SIZE)
    {
      SignalSnapshot current = snapshot;
      for (int offset = 0; offset < nodeIds.size(); offset += TOPOLOGY_BATCH_SIZE)
      {
        int end = Math.min(offset + TOPOLOGY_BATCH_SIZE, nodeIds.size());
        ArrayList<SignalSnapshot.Point> batchPoints = new ArrayList<>();
        for (int i = offset; i < end; ++i) batchPoints.add(diagnosticPoints.get(i));
        current = applySignalNodeCenterClusterBatch(endpoint, current, batchPoints, originLat, originLon);
      }
      return current;
    }
    return applySignalNodeCenterClusterBatch(endpoint, snapshot, diagnosticPoints, originLat, originLon);
  }

  private static SignalSnapshot applySignalNodeCenterClusterBatch(
      String endpoint, SignalSnapshot snapshot, ArrayList<SignalSnapshot.Point> diagnosticPoints,
      double originLat, double originLon)
  {
    ArrayList<Long> nodeIds = new ArrayList<>();
    for (SignalSnapshot.Point point : diagnosticPoints) nodeIds.add(point.id);
    StringBuilder ids = new StringBuilder();
    for (int i = 0; i < nodeIds.size(); ++i)
    {
      if (i > 0) ids.append(',');
      ids.append(nodeIds.get(i));
    }
    String query = "[out:json][timeout:8];node(id:" + ids + ")->.signals;"
        + "way(bn.signals)[highway]->.roads;(.roads;node(w.roads););out body qt;";
    Log.i("CB6-SIGNAL-WAY-DIAG", "stage=start node-count=" + nodeIds.size());
    try
    {
      String response = post(endpoint, query);
      Log.i("CB6-SIGNAL-WAY-DIAG", "stage=http-complete bytes=" + response.length());
      JSONObject root = new JSONObject(response);
      if (root.has("remark"))
      {
        Log.i("CB6-SIGNAL-WAY-DIAG", "stage=complete result=incomplete");
        return snapshot;
      }
      JSONArray elements = root.getJSONArray("elements");
      Log.i("CB6-SIGNAL-WAY-DIAG", "stage=elements count=" + elements.length());
      if (elements.length() == 0)
        Log.i("CB6-SIGNAL-WAY-DIAG", "stage=complete result=zero-elements");

      ArrayList<ArrayList<String>> roadWays = new ArrayList<>();
      ArrayList<Long> responseNodeIds = new ArrayList<>();
      ArrayList<Double> responseNodeLats = new ArrayList<>();
      ArrayList<Double> responseNodeLons = new ArrayList<>();
      for (int i = 0; i < elements.length(); ++i)
      {
        JSONObject element = elements.optJSONObject(i);
        if (element == null || !"node".equals(element.optString("type"))) continue;
        long responseNodeId = element.optLong("id", -1);
        if (responseNodeId <= 0 || !element.has("lat") || !element.has("lon")) continue;
        responseNodeIds.add(responseNodeId);
        responseNodeLats.add(element.optDouble("lat"));
        responseNodeLons.add(element.optDouble("lon"));
      }

      ArrayList<Long> roadWayIds = new ArrayList<>();
      ArrayList<ArrayList<Long>> roadWayNodes = new ArrayList<>();
      for (int i = 0; i < nodeIds.size(); ++i) roadWays.add(new ArrayList<>());

      for (int i = 0; i < elements.length(); ++i)
      {
        JSONObject way = elements.optJSONObject(i);
        if (way == null || !"way".equals(way.optString("type"))) continue;
        JSONObject tags = way.optJSONObject("tags");
        JSONArray nodes = way.optJSONArray("nodes");
        if (tags == null || nodes == null) continue;
        long wayId = way.optLong("id", -1);
        String highway = tags.optString("highway");
        boolean roadWay = !"footway".equals(highway) && !"path".equals(highway)
            && !"pedestrian".equals(highway) && !"steps".equals(highway)
            && !"cycleway".equals(highway);
        if (roadWay)
        {
          ArrayList<Long> wayNodes = new ArrayList<>();
          for (int j = 0; j < nodes.length(); ++j) wayNodes.add(nodes.optLong(j, -1));
          roadWayIds.add(wayId);
          roadWayNodes.add(wayNodes);
        }
        for (int j = 0; j < nodes.length(); ++j)
        {
          long nodeId = nodes.optLong(j, -1);
          int nodeIndex = nodeIds.indexOf(nodeId);
          if (nodeIndex < 0) continue;
          Log.i("CB6-SIGNAL-WAY-DIAG", "way=" + wayId + " highway=" + highway
              + " node=" + nodeId + " index=" + j);
          if (roadWay) roadWays.get(nodeIndex).add(wayId + ":" + highway);
        }
      }

      float[] pairDistance = new float[1];
      boolean[][] groupLinks = new boolean[diagnosticPoints.size()][diagnosticPoints.size()];
      ArrayList<Long> centerCandidateIds = new ArrayList<>();
      ArrayList<ArrayList<Integer>> centerCandidateMembers = new ArrayList<>();
      boolean[][] separatedParallelLinks =
          new boolean[diagnosticPoints.size()][diagnosticPoints.size()];
      for (int i = 0; i < diagnosticPoints.size(); ++i)
      {
        SignalSnapshot.Point a = diagnosticPoints.get(i);
        for (int j = i + 1; j < diagnosticPoints.size(); ++j)
        {
          SignalSnapshot.Point b = diagnosticPoints.get(j);
          Location.distanceBetween(a.lat, a.lon, b.lat, b.lon, pairDistance);
          if (pairDistance[0] > 30.0f) continue;
          ArrayList<String> aWays = roadWays.get(i);
          ArrayList<String> bWays = roadWays.get(j);
          boolean shared = false;
          for (String aWay : aWays)
          {
            int separator = aWay.indexOf(':');
            String aWayId = separator >= 0 ? aWay.substring(0, separator) : aWay;
            for (String bWay : bWays)
            {
              int bSeparator = bWay.indexOf(':');
              String bWayId = bSeparator >= 0 ? bWay.substring(0, bSeparator) : bWay;
              if (aWayId.equals(bWayId)) shared = true;
            }
          }
          ArrayList<Long> commonRoadNodes = new ArrayList<>();
          for (String aWay : aWays)
          {
            long aWayId = Long.parseLong(aWay.substring(0, aWay.indexOf(':')));
            int aWayIndex = roadWayIds.indexOf(aWayId);
            if (aWayIndex < 0) continue;
            for (String bWay : bWays)
            {
              long bWayId = Long.parseLong(bWay.substring(0, bWay.indexOf(':')));
              int bWayIndex = roadWayIds.indexOf(bWayId);
              if (bWayIndex < 0 || aWayId == bWayId) continue;
              for (Long roadNode : roadWayNodes.get(aWayIndex))
              {
                if (roadNode > 0 && roadWayNodes.get(bWayIndex).contains(roadNode)
                    && !commonRoadNodes.contains(roadNode))
                  commonRoadNodes.add(roadNode);
              }
            }
          }
          for (Long commonRoadNode : commonRoadNodes)
          {
            int commonIndex = responseNodeIds.indexOf(commonRoadNode);
            if (commonIndex < 0) continue;
            double commonLat = responseNodeLats.get(commonIndex);
            double commonLon = responseNodeLons.get(commonIndex);
            float[] aToCommon = new float[1];
            float[] bToCommon = new float[1];
            Location.distanceBetween(a.lat, a.lon, commonLat, commonLon, aToCommon);
            Location.distanceBetween(b.lat, b.lon, commonLat, commonLon, bToCommon);
            int centerCandidateIndex = centerCandidateIds.indexOf(commonRoadNode);
            if (centerCandidateIndex < 0)
            {
              centerCandidateIds.add(commonRoadNode);
              centerCandidateMembers.add(new ArrayList<Integer>());
              centerCandidateIndex = centerCandidateIds.size() - 1;
            }
            if (!centerCandidateMembers.get(centerCandidateIndex).contains(i))
              centerCandidateMembers.get(centerCandidateIndex).add(i);
            if (!centerCandidateMembers.get(centerCandidateIndex).contains(j))
              centerCandidateMembers.get(centerCandidateIndex).add(j);
            Log.i("CB6-SIGNAL-WAY-DIAG", "common-road-node=" + commonRoadNode
                + " lat=" + commonLat + " lon=" + commonLon
                + " pair-a=" + a.id + " a-distance=" + aToCommon[0]
                + " pair-b=" + b.id + " b-distance=" + bToCommon[0]);
          }
          if (!shared && commonRoadNodes.isEmpty())
          {
            float minRoadNodeDistance = Float.MAX_VALUE;
            long minAWayId = -1;
            long minBWayId = -1;
            long minANodeId = -1;
            long minBNodeId = -1;
            float[] roadNodeDistance = new float[1];
            int nearRoadNodePairCount = 0;
            ArrayList<String> nearRoadNodePairs = new ArrayList<>();
            long nearAWayId = -1;
            long nearBWayId = -1;
            ArrayList<Long> nearANodes = new ArrayList<>();
            ArrayList<Long> nearBNodes = new ArrayList<>();
            for (String aWay : aWays)
            {
              long aWayId = Long.parseLong(aWay.substring(0, aWay.indexOf(':')));
              int aWayIndex = roadWayIds.indexOf(aWayId);
              if (aWayIndex < 0) continue;
              for (String bWay : bWays)
              {
                long bWayId = Long.parseLong(bWay.substring(0, bWay.indexOf(':')));
                int bWayIndex = roadWayIds.indexOf(bWayId);
                if (bWayIndex < 0) continue;
                for (Long aRoadNode : roadWayNodes.get(aWayIndex))
                {
                  int aNodeIndex = responseNodeIds.indexOf(aRoadNode);
                  if (aNodeIndex < 0) continue;
                  for (Long bRoadNode : roadWayNodes.get(bWayIndex))
                  {
                    int bNodeIndex = responseNodeIds.indexOf(bRoadNode);
                    if (bNodeIndex < 0) continue;
                    Location.distanceBetween(responseNodeLats.get(aNodeIndex),
                        responseNodeLons.get(aNodeIndex), responseNodeLats.get(bNodeIndex),
                        responseNodeLons.get(bNodeIndex), roadNodeDistance);
                    if (roadNodeDistance[0] <= 15.0f)
                    {
                      ++nearRoadNodePairCount;
                      nearRoadNodePairs.add(aRoadNode + ":" + bRoadNode + ":" + roadNodeDistance[0]);
                      if (!nearANodes.contains(aRoadNode)) nearANodes.add(aRoadNode);
                      if (!nearBNodes.contains(bRoadNode)) nearBNodes.add(bRoadNode);
                      nearAWayId = aWayId;
                      nearBWayId = bWayId;
                    }
                    if (roadNodeDistance[0] < minRoadNodeDistance)
                    {
                      minRoadNodeDistance = roadNodeDistance[0];
                      minAWayId = aWayId;
                      minBWayId = bWayId;
                      minANodeId = aRoadNode;
                      minBNodeId = bRoadNode;
                    }
                  }
                }
              }
            }
            if (minAWayId > 0)
            {
              float aNearSpan = 0.0f;
              float bNearSpan = 0.0f;
              if (nearAWayId > 0)
              {
                int aNearWayIndex = roadWayIds.indexOf(nearAWayId);
                int bNearWayIndex = roadWayIds.indexOf(nearBWayId);
                if (aNearWayIndex >= 0)
                {
                  ArrayList<Long> nodes = roadWayNodes.get(aNearWayIndex);
                  for (int n = 1; n < nodes.size(); ++n)
                  {
                    if (!nearANodes.contains(nodes.get(n - 1)) || !nearANodes.contains(nodes.get(n))) continue;
                    int p = responseNodeIds.indexOf(nodes.get(n - 1));
                    int q = responseNodeIds.indexOf(nodes.get(n));
                    if (p < 0 || q < 0) continue;
                    Location.distanceBetween(responseNodeLats.get(p), responseNodeLons.get(p),
                        responseNodeLats.get(q), responseNodeLons.get(q), roadNodeDistance);
                    aNearSpan += roadNodeDistance[0];
                  }
                }
                if (bNearWayIndex >= 0)
                {
                  ArrayList<Long> nodes = roadWayNodes.get(bNearWayIndex);
                  for (int n = 1; n < nodes.size(); ++n)
                  {
                    if (!nearBNodes.contains(nodes.get(n - 1)) || !nearBNodes.contains(nodes.get(n))) continue;
                    int p = responseNodeIds.indexOf(nodes.get(n - 1));
                    int q = responseNodeIds.indexOf(nodes.get(n));
                    if (p < 0 || q < 0) continue;
                    Location.distanceBetween(responseNodeLats.get(p), responseNodeLons.get(p),
                        responseNodeLats.get(q), responseNodeLons.get(q), roadNodeDistance);
                    bNearSpan += roadNodeDistance[0];
                  }
                }
                if (aNearSpan >= 100.0f && bNearSpan >= 100.0f)
                  separatedParallelLinks[i][j] = separatedParallelLinks[j][i] = true;
                Log.i("CB6-SIGNAL-WAY-DIAG", "separate-way-span pair-a=" + a.id
                    + " pair-b=" + b.id + " a-way=" + nearAWayId + " b-way=" + nearBWayId
                    + " a-near-nodes=" + nearANodes + " b-near-nodes=" + nearBNodes
                    + " a-near-span=" + aNearSpan + " b-near-span=" + bNearSpan);
              }
              Log.i("CB6-SIGNAL-WAY-DIAG", "separate-way-shape pair-a=" + a.id
                  + " pair-b=" + b.id + " near-15m-count=" + nearRoadNodePairCount
                  + " near-15m-node-pairs=" + nearRoadNodePairs);
              Log.i("CB6-SIGNAL-WAY-DIAG", "separate-way pair-a=" + a.id
                  + " pair-b=" + b.id + " a-way=" + minAWayId + " b-way=" + minBWayId
                  + " a-node=" + minANodeId + " b-node=" + minBNodeId
                  + " min-node-distance=" + minRoadNodeDistance);
            }
          }
          boolean groupLink = shared || !commonRoadNodes.isEmpty();
          groupLinks[i][j] = groupLinks[j][i] = groupLink;
          Log.i("CB6-SIGNAL-WAY-DIAG", "pair-a=" + a.id + " pair-b=" + b.id
              + " distance=" + pairDistance[0] + " a-road-ways=" + aWays
              + " b-road-ways=" + bWays + " shared-road-way=" + shared
              + " connected-road-way=" + !commonRoadNodes.isEmpty()
              + " common-road-nodes=" + commonRoadNodes
              + " group-link=" + groupLink);
        }
      }

      boolean[] mergedCenter = new boolean[centerCandidateIds.size()];
      ArrayList<Integer> mergedCenterBases = new ArrayList<>();
      ArrayList<ArrayList<Integer>> mergedCenterDisplayMembers = new ArrayList<>();
      int mergedCenterClusterId = 0;
      for (int base = 0; base < centerCandidateIds.size(); ++base)
      {
        if (mergedCenter[base]) continue;
        mergedCenter[base] = true;
        ArrayList<Long> mergedCenterIds = new ArrayList<>();
        mergedCenterIds.add(centerCandidateIds.get(base));
        ArrayList<Integer> mergedMembers = new ArrayList<>();
        for (Integer member : centerCandidateMembers.get(base))
          if (!mergedMembers.contains(member)) mergedMembers.add(member);
        int baseNodeIndex = responseNodeIds.indexOf(centerCandidateIds.get(base));
        if (baseNodeIndex >= 0)
        {
          for (int candidate = base + 1; candidate < centerCandidateIds.size(); ++candidate)
          {
            if (mergedCenter[candidate]) continue;
            int candidateNodeIndex = responseNodeIds.indexOf(centerCandidateIds.get(candidate));
            if (candidateNodeIndex < 0) continue;
            Location.distanceBetween(responseNodeLats.get(baseNodeIndex),
                responseNodeLons.get(baseNodeIndex), responseNodeLats.get(candidateNodeIndex),
                responseNodeLons.get(candidateNodeIndex), pairDistance);
            if (pairDistance[0] > 15.0f) continue;
            mergedCenter[candidate] = true;
            mergedCenterIds.add(centerCandidateIds.get(candidate));
            for (Integer member : centerCandidateMembers.get(candidate))
              if (!mergedMembers.contains(member)) mergedMembers.add(member);
          }
        }
        ArrayList<Long> mergedMemberIds = new ArrayList<>();
        float mergedMaxDiameter = 0.0f;
        for (int m = 0; m < mergedMembers.size(); ++m)
        {
          SignalSnapshot.Point a = diagnosticPoints.get(mergedMembers.get(m));
          mergedMemberIds.add(a.id);
          for (int n = m + 1; n < mergedMembers.size(); ++n)
          {
            SignalSnapshot.Point b = diagnosticPoints.get(mergedMembers.get(n));
            Location.distanceBetween(a.lat, a.lon, b.lat, b.lon, pairDistance);
            if (pairDistance[0] > mergedMaxDiameter) mergedMaxDiameter = pairDistance[0];
          }
        }
        mergedCenterBases.add(base);
        mergedCenterDisplayMembers.add(new ArrayList<Integer>(mergedMembers));
        Log.i("CB6-SIGNAL-WAY-DIAG", "merged-center-cluster=" + mergedCenterClusterId
            + " base-center-node=" + centerCandidateIds.get(base)
            + " merged-center-nodes=" + mergedCenterIds + " members=" + mergedMemberIds
            + " member-count=" + mergedMembers.size()
            + " max-diameter=" + mergedMaxDiameter);
        ++mergedCenterClusterId;
      }

      // Production display connection: use the already-fetched diagnostic road response only.
      // Each cluster is anchored to its base center; merged centers never become new anchors.
      boolean[] displayMemberAssigned = new boolean[diagnosticPoints.size()];
      ArrayList<SignalSnapshot.Point> displayPoints = new ArrayList<>(snapshot.points);
      for (int cluster = 0; cluster < mergedCenterBases.size(); ++cluster)
      {
        int base = mergedCenterBases.get(cluster);
        ArrayList<Integer> clusterMembers = mergedCenterDisplayMembers.get(cluster);
        int baseNodeIndex = responseNodeIds.indexOf(centerCandidateIds.get(base));
        if (baseNodeIndex < 0) continue;
        ArrayList<Integer> unassignedMembers = new ArrayList<>();
        for (Integer member : clusterMembers)
          if (!displayMemberAssigned[member]) unassignedMembers.add(member);
        if (unassignedMembers.size() < 2) continue;
        SignalSnapshot.Point representative = diagnosticPoints.get(unassignedMembers.get(0));
        for (Integer member : unassignedMembers)
        {
          displayMemberAssigned[member] = true;
          displayPoints.remove(diagnosticPoints.get(member));
        }
        float[] centerDistance = new float[1];
        double centerLat = responseNodeLats.get(baseNodeIndex);
        double centerLon = responseNodeLons.get(baseNodeIndex);
        Location.distanceBetween(originLat, originLon, centerLat, centerLon, centerDistance);
        displayPoints.add(new SignalSnapshot.Point(representative.id, centerLat, centerLon,
            centerDistance[0]));
        Log.i("CB6-SIGNAL-WAY-DIAG", "display-center-node=" + centerCandidateIds.get(base)
            + " representative-signal=" + representative.id
            + " replaced-member-count=" + unassignedMembers.size());
      }

      SignalSnapshot displaySnapshot = new SignalSnapshot(displayPoints);

      boolean[] centerAssigned = new boolean[diagnosticPoints.size()];
      int centerClusterId = 0;
      for (int center = 0; center < centerCandidateIds.size(); ++center)
      {
        ArrayList<Integer> members = centerCandidateMembers.get(center);
        if (members.isEmpty()) continue;
        ArrayList<Long> memberIds = new ArrayList<>();
        float maxDiameter = 0.0f;
        for (int m = 0; m < members.size(); ++m)
        {
          int member = members.get(m);
          centerAssigned[member] = true;
          SignalSnapshot.Point a = diagnosticPoints.get(member);
          memberIds.add(a.id);
          for (int n = m + 1; n < members.size(); ++n)
          {
            SignalSnapshot.Point b = diagnosticPoints.get(members.get(n));
            Location.distanceBetween(a.lat, a.lon, b.lat, b.lon, pairDistance);
            if (pairDistance[0] > maxDiameter) maxDiameter = pairDistance[0];
          }
        }
        Log.i("CB6-SIGNAL-WAY-DIAG", "center-cluster=" + centerClusterId
            + " center-node=" + centerCandidateIds.get(center) + " members=" + memberIds
            + " member-count=" + members.size() + " max-diameter=" + maxDiameter);
        ++centerClusterId;
      }
      for (int i = 0; i < diagnosticPoints.size(); ++i)
      {
        if (centerAssigned[i]) continue;
        for (int j = i + 1; j < diagnosticPoints.size(); ++j)
        {
          if (centerAssigned[j] || !separatedParallelLinks[i][j]) continue;
          ArrayList<Long> memberIds = new ArrayList<>();
          memberIds.add(diagnosticPoints.get(i).id);
          memberIds.add(diagnosticPoints.get(j).id);
          Location.distanceBetween(diagnosticPoints.get(i).lat, diagnosticPoints.get(i).lon,
              diagnosticPoints.get(j).lat, diagnosticPoints.get(j).lon, pairDistance);
          Log.i("CB6-SIGNAL-WAY-DIAG", "center-cluster=" + centerClusterId
              + " center-node=-1 members=" + memberIds
              + " member-count=2 max-diameter=" + pairDistance[0]
              + " supplement=separated-parallel-way");
          centerAssigned[i] = true;
          centerAssigned[j] = true;
          ++centerClusterId;
          break;
        }
      }

      boolean[] grouped = new boolean[diagnosticPoints.size()];
      int groupId = 0;
      for (int seed = 0; seed < diagnosticPoints.size(); ++seed)
      {
        if (grouped[seed]) continue;
        ArrayList<Integer> members = new ArrayList<>();
        ArrayList<Integer> queue = new ArrayList<>();
        grouped[seed] = true;
        queue.add(seed);
        for (int q = 0; q < queue.size(); ++q)
        {
          int current = queue.get(q);
          members.add(current);
          for (int candidate = 0; candidate < diagnosticPoints.size(); ++candidate)
          {
            if (!grouped[candidate] && groupLinks[current][candidate])
            {
              grouped[candidate] = true;
              queue.add(candidate);
            }
          }
        }
        ArrayList<Long> memberIds = new ArrayList<>();
        float maxDiameter = 0.0f;
        for (int i = 0; i < members.size(); ++i)
        {
          SignalSnapshot.Point a = diagnosticPoints.get(members.get(i));
          memberIds.add(a.id);
          for (int j = i + 1; j < members.size(); ++j)
          {
            SignalSnapshot.Point b = diagnosticPoints.get(members.get(j));
            Location.distanceBetween(a.lat, a.lon, b.lat, b.lon, pairDistance);
            if (pairDistance[0] > maxDiameter) maxDiameter = pairDistance[0];
          }
        }
        Log.i("CB6-SIGNAL-WAY-DIAG", "group=" + groupId + " members=" + memberIds
            + " member-count=" + members.size() + " max-diameter=" + maxDiameter);
        ++groupId;
      }
      return displaySnapshot;
    }
    catch (Exception error)
    {
      Log.i("CB6-SIGNAL-WAY-DIAG", "stage=exception type="
          + error.getClass().getSimpleName() + " message=" + String.valueOf(error.getMessage()));
      return snapshot;
    }
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
