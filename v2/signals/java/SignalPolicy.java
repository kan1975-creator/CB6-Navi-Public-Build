package app.organicmaps.cb6.signals;

/** Frozen Run #65 policy. Pure functions; no Android, network or renderer state. */
public final class SignalPolicy
{
  public static final int RADIUS_M = 3000;
  public static final int MAX_POINTS = 1400;
  public static final long REFRESH_MS = 45 * 1000L;
  public static final long RETRY_MS = 12 * 1000L;
  public static final float MOVEMENT_M = 250.0f;
  public static final float FORWARD_MAX_M = 450.0f;
  public static final float FORWARD_CONE_DEG = 45.0f;
  public static final long CACHE_MAX_MS = 24 * 60 * 60 * 1000L;

  private SignalPolicy() {}

  public static boolean validCoordinate(double lat, double lon)
  {
    return Double.isFinite(lat) && Double.isFinite(lon)
        && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
  }

  public static boolean forward(float distance, float targetBearing, float bearing, boolean hasBearing)
  {
    if (!hasBearing || !Float.isFinite(bearing) || !Float.isFinite(targetBearing)
        || !Float.isFinite(distance) || distance < 0 || distance > FORWARD_MAX_M)
      return false;
    float delta = ((targetBearing - bearing) % 360.0f + 540.0f) % 360.0f - 180.0f;
    return Math.abs(delta) <= FORWARD_CONE_DEG;
  }

  public static boolean shouldRequest(long now, long lastAttempt, boolean attempted,
                                      boolean failed, float moved)
  {
    if (!attempted) return true;
    long elapsed = now - lastAttempt;
    if (elapsed < RETRY_MS) return false;
    return failed || elapsed >= REFRESH_MS || moved >= MOVEMENT_M;
  }
}
