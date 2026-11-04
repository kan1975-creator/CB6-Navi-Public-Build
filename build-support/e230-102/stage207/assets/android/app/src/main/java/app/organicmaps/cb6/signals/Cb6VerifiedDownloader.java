package app.organicmaps.cb6.signals;

import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import java.util.Locale;
/** Bounded HTTPS-only downloader; caller owns cleanup. Allowlisted HTTPS redirects only; no cleartext fallback. */
public final class Cb6VerifiedDownloader {
  private Cb6VerifiedDownloader() {}
  public static byte[] small(String url, int maximum) throws Exception {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    fetch(url, out, maximum);
    return out.toByteArray();
  }
  public static void file(String url, File target, long maximum) throws Exception {
    boolean ok = false;
    try (FileOutputStream out = new FileOutputStream(target)) {
      fetch(url, out, maximum); out.getFD().sync(); ok = true;
    } finally { if (!ok) target.delete(); }
  }
  private static void fetch(String url, OutputStream out, long maximum) throws Exception {
    if (maximum <= 0) throw new IOException("Invalid size limit");
    URL current = new URL(url);
    if (!trustedHost(current, true)) throw new IOException("Untrusted origin");
    for (int hop = 0; hop <= 5; hop++) {
      HttpURLConnection conn = (HttpURLConnection) current.openConnection();
      conn.setInstanceFollowRedirects(false);
      conn.setConnectTimeout(15000); conn.setReadTimeout(30000);
      try {
        int status = conn.getResponseCode();
        if (status == 301 || status == 302 || status == 303 || status == 307 || status == 308) {
          if (hop == 5) throw new IOException("Too many redirects");
          String location = conn.getHeaderField("Location");
          if (location == null) throw new IOException("Missing redirect target");
          URL next = new URL(current, location);
          if (!trustedHost(next, false)) throw new IOException("Untrusted redirect target");
          current = next;
          continue;
        }
        if (status != 200) throw new IOException("HTTP " + status);
        long declared = conn.getContentLengthLong();
        if (declared > maximum) throw new IOException("Response too large");
        try (InputStream in = conn.getInputStream()) {
          byte[] buf = new byte[16384]; long count = 0; int n;
          while ((n = in.read(buf)) != -1) {
            if (n > maximum - count) throw new IOException("Download exceeds limit");
            count += n;
            out.write(buf, 0, n);
          }
        }
        return;
      } finally { conn.disconnect(); }
    }
    throw new IOException("Redirect limit reached");
  }
  private static boolean trustedHost(URL url, boolean origin) {
    if (!"https".equalsIgnoreCase(url.getProtocol()) || url.getUserInfo() != null
        || (url.getPort() != -1 && url.getPort() != 443)) return false;
    String host = url.getHost().toLowerCase(Locale.ROOT);
    if (origin) return "github.com".equals(host);
    return "github.com".equals(host) || "release-assets.githubusercontent.com".equals(host)
        || "objects.githubusercontent.com".equals(host);
  }
  public static String sha256(File file) throws Exception {
    MessageDigest md = MessageDigest.getInstance("SHA-256");
    try (InputStream in = new FileInputStream(file)) {
      byte[] b = new byte[16384]; int n;
      while ((n = in.read(b)) != -1) md.update(b, 0, n);
    }
    StringBuilder s = new StringBuilder();
    for (byte b : md.digest()) s.append(String.format(Locale.US, "%02x", b & 255));
    return s.toString();
  }
}
