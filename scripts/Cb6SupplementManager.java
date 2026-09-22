package app.organicmaps;

import android.content.Context;
import android.content.SharedPreferences;
import android.location.Location;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;

import app.organicmaps.sdk.Framework;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** CB6 supplemental POIs with explicit traffic-signal diagnostics. */
public final class Cb6SupplementManager
{
  private static final String TAG = "CB6Supplement";
  private static final String PREF = "cb6_supplement";
  private static final String CACHE = "cache";
  private static final String CACHE_TIME = "cache_time";
  private static final long REFRESH_MS = 10 * 60 * 1000L;
  private static final long CACHE_MAX_MS = 24 * 60 * 60 * 1000L;
  private static final float REFRESH_DISTANCE_M = 2200.0f;
  private static final int MAX_POINTS = 2200;
  private static final int KIND_SIGNAL_FULL = 7;
  private static final int KIND_SIGNAL_CLUSTER = 20;
  private static final int MAX_SIGNAL_POINTS = 1400;

  private final Context mContext;
  private final ExecutorService mExecutor = Executors.newSingleThreadExecutor();
  private final Handler mMain = new Handler(Looper.getMainLooper());

  private long mLastRequestTime;
  private double mLastLat = Double.NaN;
  private double mLastLon = Double.NaN;
  private boolean mCacheApplied;
  private double mDiagnosticLat = Double.NaN;
  private double mDiagnosticLon = Double.NaN;

  public Cb6SupplementManager(@NonNull Context context) { mContext = context.getApplicationContext(); }

  public void onLocation(@NonNull Location location)
  {
    if (Double.isNaN(mDiagnosticLat) || Double.isNaN(mDiagnosticLon))
    {
      mDiagnosticLat = location.getLatitude() + 0.00108;
      mDiagnosticLon = location.getLongitude();
      postDiagnosticOnly();
    }
    if (!mCacheApplied) { mCacheApplied = true; applySavedCache(); }
    final long now = System.currentTimeMillis();
    final double lat = location.getLatitude(), lon = location.getLongitude();
    if (now - mLastRequestTime < REFRESH_MS && !movedEnough(lat, lon)) return;
    mLastRequestTime = now; mLastLat = lat; mLastLon = lon;
    mExecutor.execute(() -> refresh(lat, lon));
  }

  public void reapplySavedMarks() { applySavedCache(); if (!hasUsableCache()) postDiagnosticOnly(); }

  private boolean movedEnough(double lat, double lon)
  {
    if (Double.isNaN(mLastLat) || Double.isNaN(mLastLon)) return true;
    float[] result = new float[1];
    Location.distanceBetween(mLastLat, mLastLon, lat, lon, result);
    return result[0] >= REFRESH_DISTANCE_M;
  }

  private boolean hasUsableCache()
  {
    SharedPreferences p=mContext.getSharedPreferences(PREF,Context.MODE_PRIVATE);
    long age=System.currentTimeMillis()-p.getLong(CACHE_TIME,0); String json=p.getString(CACHE,"");
    return age>=0&&age<=CACHE_MAX_MS&&json!=null&&!json.isEmpty();
  }

  private void applySavedCache()
  {
    SharedPreferences p=mContext.getSharedPreferences(PREF,Context.MODE_PRIVATE);
    long age=System.currentTimeMillis()-p.getLong(CACHE_TIME,0); if(age<0||age>CACHE_MAX_MS)return;
    String json=p.getString(CACHE,""); if(json==null||json.isEmpty())return;
    try { Points points=parseCached(new JSONArray(json)); postPoints(points,"CACHE"); }
    catch(Exception e){ Log.w(TAG,"cache parse failed",e); showStatus("SIG CACHE: 読込失敗"); postDiagnosticOnly(); }
  }

  private void refresh(double lat,double lon)
  {
    String query=buildQuery(lat,lon);
    String[] endpoints={"https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter","https://overpass.nchc.org.tw/api/interpreter"};
    String lastError="";
    for(String endpoint:endpoints) try {
      Points points=parseOverpass(new JSONObject(post(endpoint,query)));
      if(points.signalCount()==0) throw new IllegalStateException("Overpass returned zero traffic signals");
      mContext.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putString(CACHE,points.toJson().toString()).putLong(CACHE_TIME,System.currentTimeMillis()).apply();
      postPoints(points,"NET"); return;
    } catch(Exception e){ lastError=e.getClass().getSimpleName()+": "+String.valueOf(e.getMessage()); Log.w(TAG,"endpoint failed: "+endpoint,e); }
    showStatus("SIG NET: 取得失敗 "+lastError); mLastRequestTime=System.currentTimeMillis()-REFRESH_MS+60_000L; applySavedCache(); if(!hasUsableCache())postDiagnosticOnly();
  }

  private void postDiagnosticOnly()
  {
    if(Double.isNaN(mDiagnosticLat)||Double.isNaN(mDiagnosticLon))return;
    mMain.post(()->{ Framework.nativeSetCb6DrivingMarks(new double[]{mDiagnosticLat},new double[]{mDiagnosticLon},new int[]{KIND_SIGNAL_FULL}); showStatus("SIG TEST: 強制信号1件をJNIへ維持"); });
  }

  private void postPoints(@NonNull Points points,@NonNull String source)
  {
    mMain.post(()->{ Points merged=points.copy(); if(!Double.isNaN(mDiagnosticLat)&&!Double.isNaN(mDiagnosticLon))merged.add(mDiagnosticLat,mDiagnosticLon,KIND_SIGNAL_FULL); Framework.nativeSetCb6DrivingMarks(merged.lats(),merged.lons(),merged.kinds()); });
  }

  private void showStatus(@NonNull String text){mMain.post(()->Toast.makeText(mContext,text,Toast.LENGTH_LONG).show());}
  private static String buildQuery(double lat,double lon){String ll=String.format(Locale.US,"%.6f,%.6f",lat,lon);return "[out:json][timeout:25];("+"node(around:5000,"+ll+")[highway=traffic_signals];"+"nwr(around:6500,"+ll+")[shop=convenience];"+"node(around:3500,"+ll+")[highway=stop];"+");out center tags;";}
  private static String post(String endpoint,String query)throws Exception
  {
    HttpURLConnection c=(HttpURLConnection)new URL(endpoint).openConnection(); c.setConnectTimeout(10000);c.setReadTimeout(25000);c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("User-Agent","CB6-Navi/SignalDiagnostic CoMaps-supplement");c.setRequestProperty("Content-Type","application/x-www-form-urlencoded; charset=UTF-8");
    byte[] body=("data="+URLEncoder.encode(query,StandardCharsets.UTF_8.name())).getBytes(StandardCharsets.UTF_8);c.getOutputStream().write(body);int code=c.getResponseCode();InputStream in=code>=200&&code<300?c.getInputStream():c.getErrorStream();if(in==null)throw new IllegalStateException("HTTP "+code);
    try(BufferedReader br=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){StringBuilder out=new StringBuilder();String line;while((line=br.readLine())!=null)out.append(line);if(code<200||code>=300)throw new IllegalStateException("HTTP "+code);return out.toString();}finally{c.disconnect();}
  }
  private static Points parseOverpass(JSONObject root)throws Exception
  {
    Points out=new Points();JSONArray elements=root.optJSONArray("elements");if(elements==null)return out;int signalsAdded=0;
    for(int i=0;i<elements.length()&&signalsAdded<MAX_SIGNAL_POINTS;++i){JSONObject e=elements.optJSONObject(i);if(e==null)continue;JSONObject tags=e.optJSONObject("tags");if(tags==null||!"traffic_signals".equals(tags.optString("highway","")))continue;double[] pos=positionOf(e);if(pos==null)continue;out.add(pos[0],pos[1],KIND_SIGNAL_FULL);++signalsAdded;}
    for(int i=0;i<elements.length()&&out.size()<MAX_POINTS;++i){JSONObject e=elements.optJSONObject(i);if(e==null)continue;JSONObject tags=e.optJSONObject("tags");if(tags==null||!"convenience".equals(tags.optString("shop","")))continue;double[] pos=positionOf(e);if(pos!=null)out.add(pos[0],pos[1],classifyConvenience(tags));}
    for(int i=0;i<elements.length()&&out.size()<MAX_POINTS;++i){JSONObject e=elements.optJSONObject(i);if(e==null)continue;JSONObject tags=e.optJSONObject("tags");if(tags==null||!"stop".equals(tags.optString("highway","")))continue;double[] pos=positionOf(e);if(pos!=null)out.add(pos[0],pos[1],0);}return out;
  }
  private static double[] positionOf(JSONObject e){if(e.has("lat")&&e.has("lon"))return new double[]{e.optDouble("lat"),e.optDouble("lon")};JSONObject center=e.optJSONObject("center");if(center!=null&&center.has("lat")&&center.has("lon"))return new double[]{center.optDouble("lat"),center.optDouble("lon")};return null;}
  private static int classifyConvenience(JSONObject tags){String source=(tags.optString("brand","")+" "+tags.optString("name","")+" "+tags.optString("operator","")).toLowerCase(Locale.ROOT);String n=source.replace(" ","").replace("-","").replace("‐","").replace("‑","").replace("–","").replace("—","");if(n.contains("7eleven")||n.contains("セブンイレブン"))return 1;if(n.contains("familymart")||n.contains("ファミリーマート")||n.contains("ファミマ"))return 2;if(n.contains("lawson")||n.contains("ローソン"))return 3;if(n.contains("seicomart")||n.contains("セイコーマート")||n.contains("セコマ"))return 4;if(n.contains("mybasket")||n.contains("まいばすけっと"))return 5;if(n.contains("ministop")||n.contains("ミニストップ"))return 8;if(n.contains("dailyyamazaki")||n.contains("デイリーヤマザキ")||n.contains("yamazakidaily"))return 9;return 6;}
  private static Points parseCached(JSONArray a)throws Exception{Points out=new Points();for(int i=0;i<a.length()&&out.size()<MAX_POINTS;++i){JSONArray p=a.getJSONArray(i);int kind=p.getInt(2);if(!((kind>=0&&kind<=9)||kind==KIND_SIGNAL_CLUSTER))continue;out.add(p.getDouble(0),p.getDouble(1),kind);}return out;}
  private static final class Points
  {
    private final ArrayList<Double> lat=new ArrayList<>(),lon=new ArrayList<>();private final ArrayList<Integer> kind=new ArrayList<>();
    void add(double a,double o,int k){lat.add(a);lon.add(o);kind.add(k);} Points copy(){Points out=new Points();out.lat.addAll(lat);out.lon.addAll(lon);out.kind.addAll(kind);return out;}int size(){return lat.size();}int signalCount(){int n=0;for(int k:kind)if(k==KIND_SIGNAL_FULL||k==KIND_SIGNAL_CLUSTER)++n;return n;}
    double[] lats(){double[] a=new double[lat.size()];for(int i=0;i<a.length;++i)a[i]=lat.get(i);return a;}double[] lons(){double[] a=new double[lon.size()];for(int i=0;i<a.length;++i)a[i]=lon.get(i);return a;}int[] kinds(){int[] a=new int[kind.size()];for(int i=0;i<a.length;++i)a[i]=kind.get(i);return a;}JSONArray toJson(){JSONArray a=new JSONArray();for(int i=0;i<size();++i){JSONArray p=new JSONArray();p.put(lat.get(i));p.put(lon.get(i));p.put(kind.get(i));a.put(p);}return a;}
  }
}
