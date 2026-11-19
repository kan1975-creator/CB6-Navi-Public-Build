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
import java.security.MessageDigest;

/** Explicitly configured HTTPS-only download, to be invoked on background executor. */
public final class Cb6FacilityDbDownload {
  private Cb6FacilityDbDownload() {}
  static boolean valid(File file) {
    if (!file.isFile() || file.length() < 1024) return false;
    try (SQLiteDatabase db = SQLiteDatabase.openDatabase(file.getAbsolutePath(), null,
        SQLiteDatabase.OPEN_READONLY)) {
      try (Cursor c = db.rawQuery("SELECT schema_version FROM cb6_metadata LIMIT 1", null)) {
        if (!c.moveToFirst() || c.getInt(0) != 1 || c.moveToNext()) return false;
      }
      try (Cursor c = db.rawQuery("SELECT lat,lon,category FROM facilities LIMIT 1", null)) {
        return c.getColumnCount() == 3;
      }
    } catch (Exception e) { return false; }
  }
  /** Optional packaged config, two UTF-8 lines: HTTPS URL then SHA-256.
   *  Missing config is normal: never guess a remote endpoint.
   *  Invoke only on the existing background worker.
   */
  public static boolean downloadConfigured(Context context) {
    try (java.io.BufferedReader in = new java.io.BufferedReader(
        new java.io.InputStreamReader(
            context.getAssets().open("cb6_facilities_download.txt"),
            java.nio.charset.StandardCharsets.UTF_8))) {
      String url = in.readLine();
      String sha = in.readLine();
      if (url == null || sha == null || in.readLine() != null) return false;
      return download(context, url.trim(), sha.trim());
    } catch (java.io.IOException e) {
      return false; // No configured facility distribution asset.
    }
  }

  public static boolean download(Context context, String url, String expectedSha256) {
    if (url == null || !url.startsWith("https://") ||
        expectedSha256 == null || !expectedSha256.matches("[a-fA-F0-9]{64}")) return false;
    File dest = new File(context.getFilesDir(), "cb6_facilities.sqlite");
    // Do not replace the active DB during a session; download is for next launch only.
    if (dest.exists()) return false;
    File tmp = new File(context.getFilesDir(), "cb6_facilities.sqlite.download");
    HttpURLConnection conn = null;
    try {
      conn = (HttpURLConnection) new URL(url).openConnection();
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
      return tmp.renameTo(dest);
    } catch (Exception e) {
      Log.w("CB6-G09", "Facility SQLite download not installed", e);
      return false;
    } finally {
      if (conn != null) conn.disconnect();
      tmp.delete();
    }
  }
}
