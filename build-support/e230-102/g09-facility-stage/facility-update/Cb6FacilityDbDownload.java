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
  // Stable latest-release URLs allow new facility data without a new APK.
  private static final String RELEASE_DB =
      "https://github.com/kan1975-creator/CB6-Navi-Public-Build/releases/download/cb6-facilities-v1/cb6_facilities.sqlite";

  public static boolean downloadConfigured(Context context) {
    String url;
    try (java.io.BufferedReader in = new java.io.BufferedReader(
        new java.io.InputStreamReader(context.getAssets().open("cb6_facilities_download.txt"),
            java.nio.charset.StandardCharsets.UTF_8))) {
      url = in.readLine();
      if (!RELEASE_DB.equals(url) || in.readLine() != null) return false;
    } catch (java.io.IOException e) { return false; }

    HttpURLConnection shaConn = null;
    try {
      shaConn = openReleaseConnection(url.replace(".sqlite", ".sha256"));
      if (shaConn.getResponseCode() != 200) return false;
      String sha;
      try (java.io.BufferedReader in = new java.io.BufferedReader(
          new java.io.InputStreamReader(shaConn.getInputStream(),
              java.nio.charset.StandardCharsets.US_ASCII))) {
        sha = in.readLine();
        if (sha == null || !sha.matches("[a-fA-F0-9]{64}") || in.readLine() != null)
          return false;
      }
      return download(context, url, sha);
    } catch (Exception e) {
      Log.w("CB6-G09", "Release checksum unavailable; active SQLite retained", e);
      return false;
    } finally {
      if (shaConn != null) shaConn.disconnect();
    }
  }

  private static HttpURLConnection openReleaseConnection(String url) throws Exception {
    URL current = new URL(url);
    for (int redirects = 0; redirects <= 5; ++redirects) {
      if (!"https".equalsIgnoreCase(current.getProtocol()) ||
          current.getUserInfo() != null) throw new java.io.IOException("Non-HTTPS URL");
      String host = current.getHost().toLowerCase(Locale.US);
      if (!host.equals("github.com") && !host.equals("release-assets.githubusercontent.com"))
        throw new java.io.IOException("Unexpected release host");
      HttpURLConnection c = (HttpURLConnection) current.openConnection();
      c.setInstanceFollowRedirects(false);
      c.setConnectTimeout(15000);
      c.setReadTimeout(30000);
      int status = c.getResponseCode();
      if (status == 200) return c;
      if (status != 301 && status != 302 && status != 303 && status != 307 && status != 308) {
        c.disconnect();
        throw new java.io.IOException("HTTP " + status);
      }
      String location = c.getHeaderField("Location");
      c.disconnect();
      if (location == null || redirects == 5) throw new java.io.IOException("Redirect limit");
      current = new URL(current, location);
    }
    throw new java.io.IOException("Redirect limit");
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
      if (!RELEASE_DB.equals(url)) return false;
      conn = openReleaseConnection(url);
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
