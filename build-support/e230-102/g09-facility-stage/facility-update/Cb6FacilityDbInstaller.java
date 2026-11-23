package app.organicmaps.cb6.facilities;

import android.content.Context;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;

/** Run on existing convenience background worker, before SQLite is selected or queried. */
public final class Cb6FacilityDbInstaller {
  private static final String ASSET = "cb6_facilities.sqlite";
  private Cb6FacilityDbInstaller() {}

  public static synchronized File ensureInstalled(Context context) {
    File dest = new File(context.getFilesDir(), ASSET);
    File pending = new File(context.getFilesDir(), ASSET + ".pending");
    File backup = new File(context.getFilesDir(), ASSET + ".backup");
    // Crash recovery: a valid active DB wins; otherwise restore the last valid backup.
    if ((!dest.isFile() || !Cb6FacilityDbDownload.valid(dest)) &&
        backup.isFile() && Cb6FacilityDbDownload.valid(backup)) {
      if (dest.exists() && !dest.delete()) return null;
      if (!backup.renameTo(dest)) return null;
    }
    // A validated active DB is the committed state on a later launch.
    if (dest.isFile() && Cb6FacilityDbDownload.valid(dest) && backup.isFile()
        && !pending.exists()) {
      if (!backup.delete()) Log.w("CB6-G09", "Stale backup retained");
    }
    if (pending.exists()) {
      if (!Cb6FacilityDbDownload.valid(pending)) {
        Log.w("CB6-G09", "Invalid pending SQLite ignored");
        pending.delete();
      } else {
        // Never remove the only valid copy; retain backup if any promotion fails.
        if (dest.isFile() && Cb6FacilityDbDownload.valid(dest)) {
          if (backup.exists() && !backup.delete()) {
            Log.w("CB6-G09", "Backup occupied; keeping active DB");
            return dest;
          }
          if (!dest.renameTo(backup)) return dest;
        }
        if (!pending.renameTo(dest) || !Cb6FacilityDbDownload.valid(dest)) {
          if (dest.exists()) dest.delete();
          if (backup.isFile() && !backup.renameTo(dest))
            Log.e("CB6-G09", "Rollback failed; backup retained");
          return dest.isFile() && Cb6FacilityDbDownload.valid(dest) ? dest : null;
        }
        // Retain valid backup as rollback candidate through next launch.
      }
    }
    if (dest.isFile() && Cb6FacilityDbDownload.valid(dest)) return dest;
    if (dest.exists()) {
      Log.w("CB6-G09", "Invalid installed facility SQLite; not overwriting");
      return null;
    }
    File temp = new File(context.getFilesDir(), ASSET + ".tmp");
    try (InputStream in = context.getAssets().open(ASSET);
         FileOutputStream out = new FileOutputStream(temp)) {
      byte[] buf = new byte[65536]; int n;
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
