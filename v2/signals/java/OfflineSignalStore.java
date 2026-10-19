package app.organicmaps.cb6.signals;

import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.net.Uri;
import android.util.Base64;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.io.FileInputStream;
import java.security.KeyFactory;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.json.JSONObject;

/** Fail-closed offline trust boundary. All methods except initial bootstrap run on worker. */
final class OfflineSignalStore
{
  static final String ASSET = "cb6/hokkaido_signals_v1.zip";
  static final int SCHEMA = 1;
  // Unset until a separately approved, out-of-chat owner key generation.
  // This is deliberately fail-closed: an unsigned file cannot be imported.
  private static final String PUBLIC_KEY_X509_BASE64 = "";
  private static final int MAX_SQLITE_BYTES = 128 * 1024 * 1024;
  private static final int MAX_MANIFEST_BYTES = 32 * 1024;
  private static final int MAX_SIG_BYTES = 512;
  private static final int MAX_ATTR_BYTES = 64 * 1024;
  private static final String[] ENTRIES = {
      "hokkaido_signals.sqlite", "manifest.json", "manifest.sig", "ATTRIBUTION.txt"};

  private final Context context;
  private final SharedPreferences prefs;
  private final File root;

  OfflineSignalStore(Context c)
  {
    context = c.getApplicationContext();
    prefs = context.getSharedPreferences("cb6_hokkaido_signals", Context.MODE_PRIVATE);
    root = new File(context.getFilesDir(), "cb6_hokkaido_signals");
  }

  static boolean configured()
  {
    return !PUBLIC_KEY_X509_BASE64.isEmpty();
  }

  private static PublicKey verifyKey() throws Exception
  {
    if (!configured()) throw new SecurityException("CB6 offline public verification key not approved");
    byte[] der = Base64.decode(PUBLIC_KEY_X509_BASE64, Base64.DEFAULT);
    PublicKey result = KeyFactory.getInstance("EC").generatePublic(new X509EncodedKeySpec(der));
    if (!(result instanceof java.security.interfaces.ECPublicKey))
      throw new SecurityException("Unexpected signature key");
    // P-256 group order differs from secp256k1; do not accept any 256-bit EC key.
    BigInteger p256order = new BigInteger(
        "FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551",16);
    java.security.spec.ECParameterSpec curve=((java.security.interfaces.ECPublicKey)result).getParams();
    if (!p256order.equals(curve.getOrder()) || curve.getCofactor()!=1
        || curve.getCurve().getField().getFieldSize()!=256)
      throw new SecurityException("Not ECDSA P-256");
    return result;
  }

  private static byte[] digest(byte[] buf) throws Exception
  {
    return MessageDigest.getInstance("SHA-256").digest(buf);
  }

  private static String digestHex(File file) throws Exception
  {
    MessageDigest md = MessageDigest.getInstance("SHA-256");
    try (InputStream in = new FileInputStream(file))
    {
      byte[] b = new byte[8192]; int n;
      while ((n = in.read(b)) != -1) md.update(b, 0, n);
    }
    StringBuilder out = new StringBuilder();
    for (byte b : md.digest()) out.append(String.format(java.util.Locale.US, "%02x", b & 0xff));
    return out.toString();
  }

  private static byte[] readMax(InputStream in, int limit) throws Exception
  {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    byte[] buf = new byte[8192]; int n;
    while ((n = in.read(buf)) != -1)
    {
      if (out.size() > limit - n) throw new SecurityException("ZIP entry exceeds permitted size");
      out.write(buf,0,n);
    }
    return out.toByteArray();
  }

  private static void copyMax(InputStream in, File dest, int max) throws Exception
  {
    try (FileOutputStream out = new FileOutputStream(dest))
    {
      byte[] buf = new byte[8192]; int total=0, n;
      while ((n = in.read(buf)) != -1)
      {
        if (total > max - n) throw new SecurityException("Database too large");
        total += n;
        out.write(buf,0,n);
      }
      out.getFD().sync();
    }
  }

  private static boolean known(String name)
  {
    for (String s : ENTRIES) if (s.equals(name)) return true;
    return false;
  }

  private static void verifySchema(File path, JSONObject manifest) throws Exception
  {
    try (SQLiteDatabase db = SQLiteDatabase.openDatabase(path.getAbsolutePath(), null,
         SQLiteDatabase.OPEN_READONLY))
    {
      try (Cursor c=db.rawQuery("PRAGMA integrity_check", null))
      {
        if (!c.moveToFirst() || !"ok".equals(c.getString(0)))
          throw new SecurityException("SQLite quick_check failed");
      }
      try (Cursor c=db.rawQuery("SELECT v FROM metadata WHERE k='schema'", null))
      {
        if (!c.moveToFirst() || !"1".equals(c.getString(0)))
          throw new SecurityException("SQLite metadata schema mismatch");
      }
      String pbf = manifest.getString("pbf_sha256");
      try (Cursor c=db.rawQuery("SELECT v FROM metadata WHERE k='pbf_sha256'", null))
      {
        if (!c.moveToFirst() || !pbf.equals(c.getString(0)))
          throw new SecurityException("PBF provenance mismatch");
      }
      long count;
      try (Cursor c=db.rawQuery("SELECT COUNT(*) FROM signals", null))
      {
        if (!c.moveToFirst()) throw new SecurityException("Signals missing");
        count=c.getLong(0);
      }
      if (count <= 0 || count != manifest.getLong("signal_count"))
        throw new SecurityException("Signals count mismatch");
      try (Cursor c=db.rawQuery("SELECT COUNT(*) FROM signal_index", null))
      {
        if (!c.moveToFirst() || c.getLong(0) != count)
          throw new SecurityException("R-tree count mismatch");
      }
      try (Cursor c=db.rawQuery("SELECT COUNT(*) FROM signals WHERE id<=0 OR lat < -90 OR lat>90 OR lon< -180 OR lon>180 OR group_id<0", null))
      {
        if (!c.moveToFirst() || c.getLong(0)!=0)
          throw new SecurityException("Invalid coordinate/identity");
      }
    }
  }

  /** Call from dedicated background thread only; never close the current database on failure. */
  synchronized int install(InputStream archive, boolean bootstrap) throws Exception
  {
    if (!configured()) throw new SecurityException("No approved public key");
    if (!root.isDirectory() && !root.mkdirs()) throw new java.io.IOException("Cannot create storage");
    File stage=File.createTempFile("incoming-", ".sqlite", root);
    Map<String,byte[]> files=new HashMap<>();
    try
    {
      boolean databaseSeen=false;
      int entries=0;
      try (ZipInputStream zip=new ZipInputStream(archive))
      {
        ZipEntry entry;
        while ((entry=zip.getNextEntry())!=null)
        {
          String name=entry.getName();
          if (++entries>ENTRIES.length || entry.isDirectory() || !known(name)
              || files.containsKey(name) || (databaseSeen && "hokkaido_signals.sqlite".equals(name)))
            throw new SecurityException("Unknown/duplicate ZIP entry");
          if ("hokkaido_signals.sqlite".equals(name))
          {
            databaseSeen=true;
            copyMax(zip, stage, MAX_SQLITE_BYTES);
          }
          else
          {
            int max="manifest.json".equals(name)?MAX_MANIFEST_BYTES:
                "manifest.sig".equals(name)?MAX_SIG_BYTES:MAX_ATTR_BYTES;
            files.put(name, readMax(zip,max));
          }
          zip.closeEntry();
        }
      }
      if (!databaseSeen || files.size()!=3 || entries!=4)
        throw new SecurityException("Missing approved ZIP entries");
      byte[] manifestBytes=files.get("manifest.json");
      byte[] signature=files.get("manifest.sig");
      Signature verifier=Signature.getInstance("SHA256withECDSA");
      verifier.initVerify(verifyKey());
      verifier.update(manifestBytes);
      if (!verifier.verify(signature)) throw new SecurityException("Invalid owner signature");
      JSONObject manifest=new JSONObject(new String(manifestBytes,StandardCharsets.UTF_8));
      if (manifest.getInt("schema")!=SCHEMA || !"hokkaido".equals(manifest.getString("region")))
        throw new SecurityException("Region/schema mismatch");
      byte[] attrSha=digest(files.get("ATTRIBUTION.txt"));
      StringBuilder attrHex=new StringBuilder();
      for (byte b : attrSha) attrHex.append(String.format(java.util.Locale.US,"%02x",b & 0xff));
      if (!attrHex.toString().equalsIgnoreCase(manifest.getString("attribution_sha256"))
          || !new String(files.get("ATTRIBUTION.txt"),StandardCharsets.UTF_8)
                   .contains("OpenStreetMap contributors"))
        throw new SecurityException("Unsigned or missing OSM attribution");
      int version=manifest.getInt("version");
      if (version<20261012 || version>99991231) throw new SecurityException("Invalid version");
      int current=prefs.getInt("version",0);
      if ((bootstrap && current>0) || (!bootstrap && version<=current))
        throw new SecurityException("Rollback or repeated version blocked");
      if (stage.length()!=manifest.getLong("sqlite_bytes") ||
          !digestHex(stage).equalsIgnoreCase(manifest.getString("sqlite_sha256")))
        throw new SecurityException("DB hash/size mismatch");
      verifySchema(stage,manifest);
      File target=new File(root,"hokkaido-"+version+"-"+digestHex(stage)+".sqlite");
      if (!target.exists())
      {
        // Stage and final file reside in the same private directory.
        if (!stage.renameTo(target)) throw new java.io.IOException("DB staging rename failed");
      }
      else if (!digestHex(target).equals(digestHex(stage)))
        throw new SecurityException("Existing data has different identity");
      String previous=prefs.getString("active", "");
      if (!prefs.edit().putString("previous", previous).putString("active",target.getName())
          .putInt("version",version).commit())
        throw new java.io.IOException("Atomic pointer commit failed");
      return version;
    }
    finally { if (stage.exists()) stage.delete(); }
  }

  synchronized void bootstrapIfNeeded() throws Exception
  {
    if (!configured() || prefs.getInt("version",0)>0) return;
    try (InputStream in=context.getAssets().open(ASSET)) { install(in,true); }
    catch (java.io.FileNotFoundException absent) { /* No first-release asset yet: fail closed. */ }
  }

  /** Cursor is consumed before handle closes; local, verified database only. */
  SignalSnapshot query(double south, double west, double north, double east) throws Exception
  {
    if (!configured() || south>north || west>east || south< -90 || north>90 || west< -180 || east>180)
      throw new SecurityException("Untrusted database or viewport");
    String active=prefs.getString("active", "");
    if (!active.matches("hokkaido-[0-9]{8}-[a-f0-9]{64}\\.sqlite"))
      return SignalSnapshot.EMPTY;
    File path=new File(root,active);
    if (!path.isFile()) throw new java.io.IOException("Missing active SQLite");
    List<SignalSnapshot.Point> points=new ArrayList<>();
    List<SignalSnapshot.Point> members=new ArrayList<>();
    List<SignalSnapshot.Point> centres=new ArrayList<>();
    double centreLat=(north+south)/2.0, centreLon=(east+west)/2.0;
    // R-tree uses float32 bounds; 0.00002 degree padding avoids false negatives.
    // Broad R-tree float32 bounds are only prefilters. Exact DOUBLE predicates
    // must be applied in SQLite BEFORE LIMIT, otherwise valid records can vanish.
    String[] args={Double.toString(north+0.00002), Double.toString(south-0.00002),
      Double.toString(east+0.00002), Double.toString(west-0.00002),
      Double.toString(south), Double.toString(north),
      Double.toString(west), Double.toString(east)};
    try (SQLiteDatabase db=SQLiteDatabase.openDatabase(path.getAbsolutePath(),null,
         SQLiteDatabase.OPEN_READONLY);
         Cursor c=db.rawQuery("SELECT s.id,s.lat,s.lon,s.group_id,s.center_lat,s.center_lon "
           +"FROM signals s JOIN signal_index r ON s.id=r.id "
           +"WHERE r.min_lat<=? AND r.max_lat>=? AND r.min_lon<=? AND r.max_lon>=? "
           +"AND s.lat>=? AND s.lat<=? AND s.lon>=? AND s.lon<=? "
           +"ORDER BY s.id LIMIT 50001",args))
    {
      while (c.moveToNext())
      {
        if (points.size()>=50000) throw new SecurityException("Viewport exceeds safety limit");
        long id=c.getLong(0),group=c.getLong(3);
        double lat=c.getDouble(1),lon=c.getDouble(2);
        if (lat<south || lat>north || lon<west || lon>east) continue;
        float[] d=new float[1];
        android.location.Location.distanceBetween(centreLat,centreLon,lat,lon,d);
        SignalSnapshot.Point signal=new SignalSnapshot.Point(id,lat,lon,d[0]);
        points.add(signal);
        if (group>0)
        {
          double y=c.getDouble(4),x=c.getDouble(5);
          if (SignalPolicy.validCoordinate(y,x))
          {
            float[] dc=new float[1];
            android.location.Location.distanceBetween(centreLat,centreLon,y,x,dc);
            members.add(signal);
            centres.add(new SignalSnapshot.Point(group,y,x,dc[0]));
          }
        }
      }
    }
    return new SignalSnapshot(points,members,centres);
  }
}
