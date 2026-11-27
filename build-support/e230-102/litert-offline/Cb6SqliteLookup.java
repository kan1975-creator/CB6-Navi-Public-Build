package jp.cb6.search;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.CancellationSignal;
import java.io.File;
import java.util.*;
import org.json.*;
/** Read-only verification of index candidates against original taxonomy. */
final class Cb6SqliteLookup {
 static boolean tagged(JSONObject data,String key){
  if(key.equals(data.optString("basic_category")))return true;
  JSONObject tax=data.optJSONObject("taxonomy");if(tax==null)return false;
  if(key.equals(tax.optString("primary")))return true;
  for(String field:new String[]{"alternates","hierarchy"}){JSONArray a=tax.optJSONArray(field);if(a!=null)for(int i=0;i<a.length();i++)if(key.equals(a.optString(i)))return true;}return false;
 }
 static boolean allowed(JSONObject data,String[] keys,BitSet selected,BitSet excluded){
  for(int i=excluded.nextSetBit(0);i>=0;i=excluded.nextSetBit(i+1))if(tagged(data,keys[i]))return false;
  for(int i=selected.nextSetBit(0);i>=0;i=selected.nextSetBit(i+1))if(tagged(data,keys[i]))return true;return false;
 }
 static List<Cb6SearchEngine.Result> lookup(File file,int[] ids,String[] keys,BitSet selected,BitSet excluded,CancellationSignal stop)throws Exception{
  List<Cb6SearchEngine.Result> out=new ArrayList<>();
  String sql="SELECT id,source,level,name,reading,aliases,address,lat,lon,precision,provenance FROM records WHERE id=? AND source='Overture' AND level='place'";
  try(SQLiteDatabase db=SQLiteDatabase.openDatabase(file.getPath(),null,SQLiteDatabase.OPEN_READONLY)){
   for(int id:ids){stop.throwIfCanceled();try(Cursor c=db.rawQuery(sql,new String[]{Integer.toString(id)},stop)){if(!c.moveToFirst())continue;if(!allowed(new JSONObject(c.getString(10)),keys,selected,excluded))continue;Cb6SearchEngine.Result p=new Cb6SearchEngine.Result(c,45);if(p.hasPosition())out.add(p);}}
  }return out;
 }
}
