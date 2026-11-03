package app.organicmaps.cb6.signals;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.location.Location;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.io.FileOutputStream;
import java.security.MessageDigest;
import java.io.FileInputStream;

/** Candidate: immutable, content-addressed SQLite. Validation is cached per process and file hash. */
public final class SQLiteSignalProvider implements SignalProvider {
  private static final int MAX_ROWS = 250000;
  private static final long MAX_NODE_ID = (1L << 61) - 1;
  private static final long WAY_NS = 1L << 62;
  private final Context context;
  public SQLiteSignalProvider(Context context) { this.context = context.getApplicationContext(); }

  static File activeFile(Context context) {
    String name = context.getSharedPreferences("cb6_signal_db", Context.MODE_PRIVATE)
        .getString("active_file", null);
    if (name == null || !name.matches("signals-[0-9a-f]{64}\\.sqlite"))
      throw new IllegalStateException("No valid active signal DB");
    File file = new File(new File(context.getFilesDir(), "cb6-signal-db"), name);
    if (!file.isFile()) throw new IllegalStateException("Active signal DB missing");
    return file;
  }

  /** All-row validation; no path-only cache. */
  static synchronized void validate(File file) throws Exception {
    if (!file.isFile()) throw new IllegalStateException("Missing DB");
    try (SQLiteDatabase db = SQLiteDatabase.openDatabase(file.getAbsolutePath(), null,
        SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS)) {
      validateOpenDatabase(db);
    }
  }

  private static void validateOpenDatabase(SQLiteDatabase db) throws Exception {
      if (db.getVersion() != 2) throw new IllegalStateException("Invalid user_version");
      try (Cursor c = db.rawQuery("PRAGMA integrity_check", null)) {
        if (!c.moveToFirst() || !"ok".equals(c.getString(0)) || c.moveToNext())
          throw new IllegalStateException("SQLite integrity_check failed");
      }
      if (!columns(db,"package_info","schema_version,dataset_version,source")
          || !columns(db,"signals","id,latitude,longitude,source_type,osm_type,osm_id")
          || !columns(db,"topology","member_id,center_id")
          || !columns(db,"r43_group_evidence","member_id,original_group_id,original_center_lat,original_center_lon"))
        throw new IllegalStateException("Unexpected schema columns");
      try (Cursor c = db.rawQuery("SELECT schema_version,dataset_version,source,"
          + "typeof(schema_version),typeof(dataset_version),typeof(source) FROM package_info",null)) {
        if (!c.moveToFirst() || !"integer".equals(c.getString(3))
            || !"text".equals(c.getString(4)) || !"text".equals(c.getString(5))
            || c.getLong(0)!=2 || c.getString(1).isEmpty() || !"osm".equals(c.getString(2))
            || c.moveToNext()) throw new IllegalStateException("Invalid package_info");
      }
      HashMap<Long,double[]> coords = new HashMap<>();
      try (Cursor c = db.rawQuery("SELECT id,latitude,longitude,source_type,osm_type,osm_id,"
          + "typeof(id),typeof(latitude),typeof(longitude),typeof(source_type),"
          + "typeof(osm_type),typeof(osm_id) FROM signals",null)) {
        int count=0;
        while(c.moveToNext()) {
          if (++count>MAX_ROWS || !"integer".equals(c.getString(6))
              || !"real".equals(c.getString(7)) || !"real".equals(c.getString(8))
              || !"text".equals(c.getString(9)) || !"text".equals(c.getString(10))
              || !"integer".equals(c.getString(11))) throw new IllegalStateException("Bad signal types/count");
          long id=c.getLong(0); double lat=c.getDouble(1),lon=c.getDouble(2);
          long osmId=c.getLong(5);
          String osmType=c.getString(4);
          if (osmId<=0 || osmId>MAX_NODE_ID || id<=0
              || ("node".equals(osmType) ? id!=osmId : ("way".equals(osmType) ? id!=(WAY_NS | osmId) : true))
              || !SignalPolicy.validCoordinate(lat,lon) || !"osm".equals(c.getString(3))
              || coords.put(id,new double[]{lat,lon})!=null)
            throw new IllegalStateException("Bad signal row");
        }
      }
      // R43 grouping is evidence only, never inferred as a topology center.
      try (Cursor c=db.rawQuery("SELECT member_id,original_group_id,original_center_lat,"
          + "original_center_lon,typeof(member_id),typeof(original_group_id),"
          + "typeof(original_center_lat),typeof(original_center_lon) FROM r43_group_evidence",null)) {
        int count=0;
        while(c.moveToNext()) {
          if (++count>MAX_ROWS || !"integer".equals(c.getString(4))
              || !"integer".equals(c.getString(5))
              || !"real".equals(c.getString(6)) || !"real".equals(c.getString(7))
              || c.getLong(1)<=0 || !coords.containsKey(c.getLong(0))
              || !SignalPolicy.validCoordinate(c.getDouble(2),c.getDouble(3)))
            throw new IllegalStateException("Invalid R43 group evidence");
        }
      }
      HashSet<Long> members=new HashSet<>();
      try (Cursor c=db.rawQuery("SELECT member_id,center_id,typeof(member_id),typeof(center_id) FROM topology",null)) {
        int count=0; float[] distance=new float[1];
        while(c.moveToNext()) {
          if (++count>MAX_ROWS || !"integer".equals(c.getString(2))
              || !"integer".equals(c.getString(3))) throw new IllegalStateException("Bad topology types/count");
          long member=c.getLong(0), center=c.getLong(1);
          double[] m=coords.get(member), k=coords.get(center);
          if (m==null || k==null || !members.add(member)) throw new IllegalStateException("Bad topology IDs");
          Location.distanceBetween(m[0],m[1],k[0],k[1],distance);
          if (member!=center && distance[0]>15.0f) throw new IllegalStateException("Topology not direct 15m");
        }
      }
      // A center must map to itself; otherwise an indirect chain may be encoded.
      try (Cursor c=db.rawQuery("SELECT t.center_id FROM topology t LEFT JOIN topology s"
          + " ON s.member_id=t.center_id AND s.center_id=t.center_id"
          + " WHERE s.member_id IS NULL LIMIT 1",null)) {
        if (c.moveToFirst()) throw new IllegalStateException("Non-root topology center");
      }
  }

  @Override public SignalSnapshot load(double lat,double lon) throws Exception {
    if (!SignalPolicy.validCoordinate(lat,lon)) throw new IllegalArgumentException("Invalid origin");
    File file=activeFile(context);
    ArrayList<SignalSnapshot.Point> points=new ArrayList<>();
    ArrayList<SignalSnapshot.Point> members=new ArrayList<>(),centers=new ArrayList<>();
    HashMap<Long,SignalSnapshot.Point> selected=new HashMap<>();
    float[] distance=new float[1];
    // Read a private, non-published snapshot: hashing and SQLite never use the mutable active path.
    File snapshot=File.createTempFile("read-snapshot-",".sqlite",context.getCacheDir());
    try {
      try (FileInputStream in=new FileInputStream(file);
           java.io.FileOutputStream out=new java.io.FileOutputStream(snapshot)) {
        byte[] buf=new byte[32768]; int n;
        while((n=in.read(buf))!=-1) out.write(buf,0,n);
        out.getFD().sync();
      }
      String expected=file.getName().substring(8,72);
      if (!expected.equals(sha256(snapshot))) throw new IllegalStateException("Active DB snapshot SHA-256 mismatch");
      // The snapshot is private to this invocation; SQLite sidecars are not copied.
      try (SQLiteDatabase db=SQLiteDatabase.openDatabase(snapshot.getAbsolutePath(),null,
          SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS)) {
        validateOpenDatabase(db);
        try (Cursor c=db.rawQuery("SELECT id,latitude,longitude FROM signals",null)) {
          while(c.moveToNext()) {
            long id=c.getLong(0); double y=c.getDouble(1),x=c.getDouble(2);
            Location.distanceBetween(lat,lon,y,x,distance);
            if (distance[0]<=SignalPolicy.RADIUS_M) {
              SignalSnapshot.Point p=new SignalSnapshot.Point(id,y,x,distance[0]);
              points.add(p); selected.put(id,p);
            }
          }
        }
        try (Cursor c=db.rawQuery("SELECT member_id,center_id FROM topology",null)) {
          while(c.moveToNext()) {
            SignalSnapshot.Point m=selected.get(c.getLong(0)),k=selected.get(c.getLong(1));
            if (m!=null && k!=null) {members.add(m);centers.add(k);}
          }
        }
      }
    } finally {
      if (!snapshot.delete() && snapshot.exists())
        throw new java.io.IOException("Private read snapshot cleanup failed");
    }
    return new SignalSnapshot(points,members,centers);
  }

  private static String sha256(File file) throws Exception {
    MessageDigest md=MessageDigest.getInstance("SHA-256");
    try (FileInputStream in=new FileInputStream(file)) {
      byte[] buffer=new byte[32768]; int n;
      while((n=in.read(buffer))!=-1) md.update(buffer,0,n);
    }
    StringBuilder hex=new StringBuilder();
    for(byte b:md.digest()) hex.append(String.format(java.util.Locale.US,"%02x",b&255));
    return hex.toString();
  }

  private static boolean columns(SQLiteDatabase db,String table,String expected) {
    StringBuilder found=new StringBuilder();
    try (Cursor c=db.rawQuery("PRAGMA table_info("+table+")",null)) {
      while(c.moveToNext()) {if(found.length()>0) found.append(','); found.append(c.getString(1));}
    }
    return expected.equals(found.toString());
  }
}
