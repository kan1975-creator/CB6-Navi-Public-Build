package app.organicmaps.cb6.facilities;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

/** Offline-only, read-only facility query. Does not modify source SQLite. */
public final class SQLiteFacilityRepository {
  private SQLiteFacilityRepository() {}

  public static final class Marks {
    public final double[] lats;
    public final double[] lons;
    public final int[] kinds;
    private Marks(double[] lats, double[] lons, int[] kinds) {
      this.lats = lats; this.lons = lons; this.kinds = kinds;
    }
  }

  private static int kind(String category) {
    if (category == null) return 0;
    switch (category) {
      case "seven_eleven": return 1;
      case "familymart": return 2;
      case "lawson": return 3;
      case "seicomart": return 4;
      case "mybasket": return 5;
      case "ministop": return 8;
      case "roadside_station": return 24;
      case "eneos": case "fuel_eneos": return 25;
      case "park": return 26;
      case "public_facility": return 27;
      case "supermarket": return 28;
      case "department_store": return 29;
      case "airport": return 30;
      case "gas_station": case "fuel": return 31;
      default: return 0;
    }
  }

  /** Must be called on a background executor. Returns only marks within the bounding box. */
  public static Marks query(File file, double minLat, double maxLat,
                            double minLon, double maxLon) {
    if (file == null || !file.isFile()) return new Marks(new double[0], new double[0], new int[0]);
    List<Double> latitudes = new ArrayList<>();
    List<Double> longitudes = new ArrayList<>();
    List<Integer> kinds = new ArrayList<>();
    try (SQLiteDatabase db = SQLiteDatabase.openDatabase(file.getAbsolutePath(), null,
        SQLiteDatabase.OPEN_READONLY)) {
      try (Cursor metadata = db.rawQuery("SELECT schema_version FROM cb6_metadata LIMIT 1", null)) {
        if (!metadata.moveToFirst() || metadata.getInt(0) != 1 || metadata.moveToNext())
          throw new IllegalStateException("Unsupported facility schema");
      }
      boolean hasBrand;
      try (Cursor columns = db.rawQuery("PRAGMA table_info(facilities)", null)) {
        boolean found = false;
        while (columns.moveToNext())
          if ("normalized_brand".equals(columns.getString(1))) found = true;
        hasBrand = found;
      }
      String select = hasBrand ? "SELECT lat, lon, category, normalized_brand FROM facilities WHERE lat BETWEEN ? AND ? "
                               : "SELECT lat, lon, category FROM facilities WHERE lat BETWEEN ? AND ? ";
      try (Cursor cursor = db.rawQuery(
          select +
          "AND lon BETWEEN ? AND ? LIMIT 100001",
          new String[]{Double.toString(minLat), Double.toString(maxLat),
              Double.toString(minLon), Double.toString(maxLon)})) {
        while (cursor.moveToNext()) {
          if (latitudes.size() >= 100000) throw new IllegalStateException("Facility limit exceeded");
          double lat = cursor.getDouble(0), lon = cursor.getDouble(1);
          String category = cursor.getString(2);
          String normalizedBrand = hasBrand ? cursor.getString(3) : null;
          int kind = ("gas_station".equals(category) || "fuel".equals(category)) && "ENEOS".equalsIgnoreCase(normalizedBrand)
              ? 25 : kind(category);
          if (!Double.isFinite(lat) || !Double.isFinite(lon) || lat < -90 || lat > 90 ||
              lon < -180 || lon > 180 || kind == 0) continue;
          latitudes.add(lat); longitudes.add(lon); kinds.add(kind);
        }
      }
    }
    int n = latitudes.size();
    double[] la = new double[n], lo = new double[n];
    int[] ki = new int[n];
    for (int i = 0; i < n; i++) {
      la[i] = latitudes.get(i); lo[i] = longitudes.get(i); ki[i] = kinds.get(i);
    }
    return new Marks(la, lo, ki);
  }
}
