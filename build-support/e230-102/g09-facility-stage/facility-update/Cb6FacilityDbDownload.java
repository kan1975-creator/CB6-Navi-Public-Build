package app.organicmaps.cb6.facilities;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;
import java.security.MessageDigest;

/** HTTPS-only facility update; staging never replaces the active DB in this session. */
public final class Cb6FacilityDbDownload {
  private Cb6FacilityDbDownload() {}
  public static boolean valid(File file) {
    if (!file.isFile() || file.length() < 1024) return false;
    try (SQLiteDatabase db = SQLiteDatabase.openDatabase(file.getAbsolutePath(), null,
        SQLiteDatabase.OPEN_READONLY)) {
      try (Cursor c = db.rawQuery("SELECT schema_version FROM cb6_metadata LIMIT 1", null)) {
        if (!c.moveToFirst() || c.getInt(0) != 1 || c.moveToNext()) return false;
      }
      try (Cursor c = db.rawQuery("SELECT lat,lon,category FROM facilities LIMIT 0", null)) {
        if (c.getColumnCount() != 3) return false;
      }
      // The previously accepted 14,934-row baseline and all 128 official stations
      // must remain represented in every accepted update. Do not infer station coordinates.
      try (Cursor c = db.rawQuery("SELECT count(*) FROM facilities", null)) {
        if (!c.moveToFirst() || c.getLong(0) < 14934L) return false;
      }
      try (Cursor c = db.rawQuery(
          "SELECT count(*) FROM facilities WHERE category = 'roadside_station'", null)) {
        if (!c.moveToFirst() || c.getLong(0) < 128L) return false;
      }
      try (Cursor c = db.rawQuery("PRAGMA quick_check", null)) {
        return c.moveToFirst() && "ok".equalsIgnoreCase(c.getString(0));
      }
    } catch (Exception e) { return false; }
  }
  public static boolean downloadConfigured(Context context) {
    try (java.io.BufferedReader in = new java.io.BufferedReader(
        new java.io.InputStreamReader(context.getAssets().open("cb6_facilities_download.txt"),
            java.nio.charset.StandardCharsets.UTF_8))) {
      String url = in.readLine(), sha = in.readLine();
      if (url == null || sha == null || in.readLine() != null) return false;
      return download(context, url.trim(), sha.trim());
    } catch (java.io.IOException e) { return false; }
  }
  public static synchronized boolean download(Context context, String url, String expectedSha256) {
    if (url == null || !url.startsWith("https://") ||
        expectedSha256 == null || !expectedSha256.matches("[a-fA-F0-9]{64}")) return false;
    File dir = context.getFilesDir();
    File pending = new File(dir, "cb6_facilities.sqlite.pending");
    File tmp = new File(dir, "cb6_facilities.sqlite.download");
    File replacement = new File(dir, "cb6_facilities.sqlite.pending.new");
    if (pending.exists() || replacement.exists()) return false; // No overwrite of staged updates.
    HttpURLConnection conn = null;
    try {
      URL endpoint = new URL(url);
      if (!"https".equalsIgnoreCase(endpoint.getProtocol()) ||
          endpoint.getUserInfo() != null || endpoint.getHost().isEmpty()) return false;
      conn = (HttpURLConnection) endpoint.openConnection();
      conn.setInstanceFollowRedirects(false);
      conn.setConnectTimeout(15000);
      conn.setReadTimeout(30000);
      if (conn.getResponseCode() != 200) return false;
      MessageDigest sha = MessageDigest.getInstance("SHA-256");
      long total = 0;
      try (InputStream in = conn.getInputStream(); FileOutputStream out = new FileOutputStream(tmp)) {
        byte[] b = new byte[65536]; int n;
        while ((n = in.read(b)) != -1) {
          total += n;
          if (total > 100L * 1024L * 1024L) throw new IllegalStateException("DB too large");
          out.write(b, 0, n); sha.update(b, 0, n);
        }
        out.getFD().sync();
      }
      StringBuilder hex = new StringBuilder();
      for (byte b : sha.digest()) hex.append(String.format(java.util.Locale.US, "%02x", b & 255));
      if (!hex.toString().equalsIgnoreCase(expectedSha256) || !valid(tmp)) return false;
      // Pending data is promoted only by the next-launch installer. Do not overwrite active DB.
      // Stage and validate before replacing an earlier pending update.
      if (!tmp.renameTo(replacement)) return false;
      if (pending.exists()) { replacement.delete(); return false; }
      return replacement.renameTo(pending);
    } catch (Exception e) {
      Log.w("CB6-G09", "Facility SQLite update staging failed", e);
      return false;
    } finally {
      if (conn != null) conn.disconnect();
      tmp.delete();
      // A failed staging attempt never leaves a partial replacement candidate.
      if (!pending.exists()) replacement.delete();
    }
  }
}
