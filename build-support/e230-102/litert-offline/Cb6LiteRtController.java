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
 public void start(String query,Location fix,Callback cb){cancel();if(closed)return;long ticket=generation;CancellationSignal stop=new CancellationSignal();signal=stop;Location origin=fix==null?null:new Location(fix);WORKER.execute(()->{List<Cb6SearchEngine.Result> rows=Collections.emptyList();String status;try{stop.throwIfCanceled();init();stop.throwIfCanceled();Cb6CategoryResolver.Decision d=core.search(query);stop.throwIfCanceled();if(d.review)status="AI: 条件を確認してください";else if(origin==null)status="AI: 現在地未取得";else{int[] ids=index.nearest(d.selected(),d.excluded(),origin.getLatitude(),origin.getLongitude(),32,stop::isCanceled);rows=Cb6SqliteLookup.lookup(Cb6SearchDb.file(app),ids,keys,d.selected(),d.excluded(),stop);status="AI: "+rows.size()+"件（分類候補）";}}catch(Exception|LinkageError e){status="AI: 処理失敗 ("+e.getClass().getSimpleName()+")";}final List<Cb6SearchEngine.Result> result=rows;final String message=status;ui.post(()->{if(!closed&&generation==ticket&&!stop.isCanceled())cb.done(result,message);});});}
 public void close(){if(closed)return;closed=true;cancel();WORKER.execute(()->{if(core!=null)core.close();core=null;index=null;keys=null;});}
}
