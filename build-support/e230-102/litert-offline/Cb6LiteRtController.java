package jp.cb6.search;

import android.content.Context;
import android.location.Location;
import android.os.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
/** Main-thread lifecycle; all inference and disposal serialized on one worker. */
public final class Cb6LiteRtController implements AutoCloseable {
 public interface Callback{void done(List<Cb6SearchEngine.Result> rows,String status);}
 private static final ExecutorService WORKER=Executors.newSingleThreadExecutor();
 private final Context app; private final Handler ui=new Handler(Looper.getMainLooper());
 private long generation; private boolean closed; private CancellationSignal signal; private Cb6LiteRtSearch core; private Cb6PlaceIndex index; private String[] keys;
 public Cb6LiteRtController(Context c){app=c.getApplicationContext();}
 private byte[] asset(String name)throws IOException{try(InputStream in=app.getAssets().open("cb6_litert/"+name);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toByteArray();}}
 private void init()throws Exception{if(core!=null)return;byte[] cats=asset("categories.tsv");String[] lines=new String(cats,StandardCharsets.UTF_8).split("\n");String[] k=new String[lines.length];for(int i=0;i<k.length;i++)k[i]=lines[i].split("\t",2)[0];Cb6PlaceIndex idx=new Cb6PlaceIndex(asset("places.bin"));File model=File.createTempFile("cb6_litert_",".tflite",app.getCacheDir());try{try(FileOutputStream o=new FileOutputStream(model)){o.write(asset("fg_model.tflite"));}core=new Cb6LiteRtSearch(model,cats,new InputStreamReader(new ByteArrayInputStream(asset("all_label_terms.tsv")),StandardCharsets.UTF_8));keys=k;index=idx;}finally{model.delete();}}
 public void cancel(){generation++;if(signal!=null)signal.cancel();signal=null;}
 private boolean meetsConstraints(Cb6SearchEngine.Result row, BitSet required, BitSet excluded) {
  if(required.isEmpty() && excluded.isEmpty()) return true;
  if(!"Overture".equals(row.source) || !"place".equals(row.level)) return false;
  try {
   org.json.JSONObject data = new org.json.JSONObject(row.provenance);
   if(data.optString("basic_category").isEmpty() && data.optJSONObject("taxonomy")==null) return false;
   for(int i=excluded.nextSetBit(0);i>=0;i=excluded.nextSetBit(i+1))
    if(Cb6SqliteLookup.tagged(data,keys[i])) return false;
   for(int i=required.nextSetBit(0);i>=0;i=required.nextSetBit(i+1))
    if(!Cb6SqliteLookup.tagged(data,keys[i])) return false;
   return true;
  } catch(org.json.JSONException e) { return false; }
 }

 private List<Cb6SearchEngine.Result> search(String query, Location origin, CancellationSignal stop) throws Exception {
  stop.throwIfCanceled();
  init();
  Cb6QueryConstraintParser.Result conditions = core.constraints(query);
  if(conditions.requiresReview()) throw new IOException("必須・除外条件を特定できません");
  Cb6CategoryResolver.Decision decision = core.search(query, conditions);
  stop.throwIfCanceled();
  File db = Cb6SearchDb.file(app);
  if(!db.isFile()) throw new IOException("検索データベースが端末にありません");
  BitSet required = conditions.required(), excluded = conditions.excluded();
  boolean restricted = !required.isEmpty() || !excluded.isEmpty();
  BitSet categories = required.isEmpty() ? decision.selected() : (BitSet) required.clone();
  if(required.isEmpty() && !excluded.isEmpty() && conditions.text.isEmpty()) {
   categories.set(0, keys.length);
   categories.andNot(excluded);
  }
  Map<Long,Cb6SearchEngine.Result> hits = new LinkedHashMap<>();
  String term = restricted ? conditions.text : query;
  if(!term.isEmpty()) {
   for(Cb6SearchEngine.Result row : Cb6SearchEngine.match(db, term, stop))
    if(meetsConstraints(row, required, excluded)) hits.put(row.id, row);
  }
  if(!categories.isEmpty() && (!restricted || term.isEmpty())) {
   if(origin==null && hits.isEmpty()) throw new IOException("周辺候補の検索に必要な現在地を取得できません");
   if(origin!=null) {
    int[] ids = index.nearest(categories, excluded, origin.getLatitude(), origin.getLongitude(), 32, stop::isCanceled);
    for(Cb6SearchEngine.Result row : Cb6SqliteLookup.lookup(db, ids, keys, categories, excluded, stop))
     if(meetsConstraints(row, required, excluded)) hits.putIfAbsent(row.id, row);
   }
  }
  return new ArrayList<>(hits.values());
 }

 public void start(String query, Location fix, Callback callback) {
  cancel();
  if(closed) return;
  long ticket = generation;
  CancellationSignal stop = new CancellationSignal();
  signal = stop;
  Location origin = fix==null ? null : new Location(fix);
  WORKER.execute(() -> {
   List<Cb6SearchEngine.Result> rows;
   String error = null;
   try {
    rows = search(query, origin, stop);
   } catch(Exception | LinkageError e) {
    rows = Collections.emptyList();
    String reason = e.getLocalizedMessage();
    error = "AI検索失敗：" + (reason==null ? e.getClass().getSimpleName() : reason);
   }
   final List<Cb6SearchEngine.Result> result = rows;
   final String status = error;
   ui.post(() -> {
    if(!closed && generation==ticket && !stop.isCanceled()) callback.done(result, status);
   });
  });
 }
 public void close(){if(closed)return;closed=true;cancel();WORKER.execute(()->{if(core!=null)core.close();core=null;index=null;keys=null;});}
}
