package app.organicmaps.cb6.facilities;

import android.content.Context;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;

/** Installs bundled facility DB once, on existing convenience background worker. */
public final class Cb6FacilityDbInstaller {
  private static final String ASSET = "cb6_facilities.sqlite";
  private Cb6FacilityDbInstaller() {}

  public static synchronized File ensureInstalled(Context context) {
    File dest = new File(context.getFilesDir(), ASSET);
    if (dest.isFile() && dest.length() > 0) return dest;
    File temp = new File(context.getFilesDir(), ASSET + ".tmp");
    try (InputStream in = context.getAssets().open(ASSET);
         FileOutputStream out = new FileOutputStream(temp)) {
      byte[] buf = new byte[65536];
      int n;
      while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
      out.getFD().sync();
    } catch (IOException e) {
      temp.delete();
      Log.w("CB6-G09", "Facility database asset not available; keeping MWM", e);
      return null;
    }
    if (!Cb6FacilityDbDownload.valid(temp) || !temp.renameTo(dest)) {
      temp.delete();
      Log.w("CB6-G09", "Facility database install failed; keeping MWM");
      return null;
    }
    return dest;
  }
}
