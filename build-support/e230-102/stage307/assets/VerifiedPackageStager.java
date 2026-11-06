package app.organicmaps.cb6.signals;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.Locale;

/** Candidate: immutable staged bytes and no-overwrite hard-link publication. */
public final class VerifiedPackageStager {
  private static final String DIAG_TAG = "Cb6PackageStager";
  private static final Object PUBLICATION_LOCK = new Object();
  private final Context context;
  public VerifiedPackageStager(Context context) {this.context=context.getApplicationContext();}
  private File directory() throws IOException {
    File dir=new File(context.getFilesDir(),"cb6-signal-db");
    if(!dir.isDirectory() && !dir.mkdirs()) throw new IOException("Cannot create DB directory");
    return dir;
  }
  public File stage(File input,String expectedSha256) throws Exception {
    if(expectedSha256==null || !expectedSha256.matches("[0-9a-f]{64}"))
      throw new IllegalArgumentException("Invalid SHA-256");
    File tmp=File.createTempFile("staging-",".tmp",directory()); boolean ok=false;
    try {
      MessageDigest digest=MessageDigest.getInstance("SHA-256");
      try(FileInputStream in=new FileInputStream(input); FileOutputStream out=new FileOutputStream(tmp)) {
        byte[] buf=new byte[32768];int n;
        while((n=in.read(buf))!=-1) {digest.update(buf,0,n);out.write(buf,0,n);}
        out.getFD().sync();
      }
      StringBuilder actual=new StringBuilder();
      for(byte b:digest.digest()) actual.append(String.format(Locale.US,"%02x",b&255));
      if(!expectedSha256.equals(actual.toString())) throw new IOException("Hash mismatch");
      SQLiteSignalProvider.validate(tmp);
      ok=true;return tmp;
    } finally {if(!ok) tmp.delete();}
  }
  private static String sha256(File file) throws Exception {
    MessageDigest md=MessageDigest.getInstance("SHA-256");
    try(FileInputStream in=new FileInputStream(file)) {
      byte[] b=new byte[32768]; int n;
      while((n=in.read(b))!=-1) md.update(b,0,n);
    }
    StringBuilder out=new StringBuilder();
    for(byte b:md.digest()) out.append(String.format(Locale.US,"%02x",b&255));
    return out.toString();
  }
  // Candidate only: JNI syscall availability and power-loss durability are unverified.
  static { System.loadLibrary("organicmaps"); }
  private static native int nativeRenameNoReplace(String source, String destination);
  /** Publish without replacing an existing generation. */
  public void activate(File staged,String expectedSha256) throws Exception {
    synchronized(PUBLICATION_LOCK) {
      activateLocked(staged,expectedSha256);
    }
  }
  private void activateLocked(File staged,String expectedSha256) throws Exception {
    if(expectedSha256==null || !expectedSha256.matches("[0-9a-f]{64}"))
      throw new IllegalArgumentException("Invalid SHA-256");
    File dir=directory();
    if(!staged.getCanonicalFile().getParentFile().equals(dir.getCanonicalFile())
        || !staged.getName().matches("staging-.*\\.tmp"))
      throw new IOException("Staged file outside private directory");
    // Verify hash again; staging files are not considered immutable until published.
    MessageDigest digest=MessageDigest.getInstance("SHA-256");
    try(FileInputStream in=new FileInputStream(staged)) {
      byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1) digest.update(b,0,n);
    }
    StringBuilder actual=new StringBuilder();
    for(byte b:digest.digest()) actual.append(String.format(Locale.US,"%02x",b&255));
    if(!expectedSha256.equals(actual.toString())) throw new IOException("Staged content changed");
    SQLiteSignalProvider.validate(staged);
    File target=new File(dir,"signals-"+expectedSha256+".sqlite");
    // renameat2(RENAME_NOREPLACE): 0 success, positive errno on failure.
    boolean created=false;
    Exception primary=null;
    try {
      int publishErrno=nativeRenameNoReplace(staged.getAbsolutePath(),target.getAbsolutePath());
      if(publishErrno==0) {
        created=true;
        Log.i(DIAG_TAG,"phase=rename-noreplace-complete");
      } else if(publishErrno==17 /* EEXIST */) {
        Log.i(DIAG_TAG,"phase=rename-noreplace-existing");
        if(!target.isFile() || !expectedSha256.equals(sha256(target)))
          throw new IOException("Existing generation mismatch; errno=17");
        SQLiteSignalProvider.validate(target);
      } else {
        throw new IOException("Non-replacing publication failed; errno="+publishErrno);
      }
      // Validate the published target before changing the active pointer.
      // If validation fails after a successful rename, retain the new generation:
      // deleting it here could race another process that already activated it.
      if(!target.isFile() || !expectedSha256.equals(sha256(target)))
        throw new IOException("Published generation hash mismatch");
      SQLiteSignalProvider.validate(target);
      SharedPreferences prefs=context.getSharedPreferences("cb6_signal_db",Context.MODE_PRIVATE);
      String previous=prefs.getString("active_file",null);
      try {
        if(!prefs.edit().putString("active_file",target.getName()).commit())
          throw new IOException("Active pointer commit returned false");
      } catch(Exception failure) {
        boolean restored=false;
        try {
          SharedPreferences.Editor rollback=prefs.edit();
          if(previous==null) rollback.remove("active_file");
          else rollback.putString("active_file",previous);
          restored=rollback.commit()
              && java.util.Objects.equals(previous,prefs.getString("active_file",null));
        } catch(Exception rollbackFailure) {failure.addSuppressed(rollbackFailure);}
        throw new IOException("Activation failed; pointer restoration="+restored
            +"; published generation retained",failure);
      }
    } catch(Exception failure) {
      primary=failure;
    } finally {
      // EEXIST validation failures must also reach staging cleanup.
      // After a successful rename the staging path no longer exists.
      if(!created) {
        try {
          if(!Files.deleteIfExists(staged.toPath()))
            throw new IOException("Staging file already absent");
        } catch(Exception cleanupFailure) {
          if(primary!=null) primary.addSuppressed(cleanupFailure);
          else primary=new IOException("Staging cleanup failed; publication state must be inspected",cleanupFailure);
        }
      }
    }
    if(primary!=null) throw primary;
    // Directory fsync, crash consistency and cross-process protection unverified: STOP.
  }
}
