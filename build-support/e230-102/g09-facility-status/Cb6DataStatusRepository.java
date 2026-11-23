package app.organicmaps.cb6.data;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import app.organicmaps.sdk.downloader.CountryItem;
import java.util.ArrayList;
import java.util.List;
import app.organicmaps.sdk.downloader.MapManager;
import java.io.File;
import java.util.EnumMap;

/** Read-only status snapshot. UNKNOWN is never promoted to success by file existence. */
public final class Cb6DataStatusRepository {
  public enum Kind { MWM, SIGNAL_SQLITE, FACILITY_SQLITE, OVERPASS }
  public enum Phase { UNKNOWN, NOT_INSTALLED, DOWNLOADING, DOWNLOADED, VERIFIED, ACTIVE, ERROR }
  public static final class Status {
    public final Kind kind;
    public final Phase phase;
    public final long downloadedBytes, totalBytes, count, updatedAt;
    public final String version, detail, error;
    public Status(Kind kind, Phase phase, long downloadedBytes, long totalBytes, long count,
                  long updatedAt, String version, String detail, String error) {
      this.kind=kind; this.phase=phase; this.downloadedBytes=downloadedBytes;
      this.totalBytes=totalBytes; this.count=count; this.updatedAt=updatedAt;
      this.version=version; this.detail=detail; this.error=error;
    }
  }
  private final Context context;
  public Cb6DataStatusRepository(Context context) { this.context=context.getApplicationContext(); }
  private static Status unknown(Kind kind, String detail) {
    return new Status(kind, Phase.UNKNOWN,-1,-1,-1,-1,"",detail,"");
  }
  public Status get(Kind kind) {
    switch(kind) {
      case MWM: return mapStatus();
      case SIGNAL_SQLITE: return signalStatus();
      case FACILITY_SQLITE: return facilityStatus();
      case OVERPASS: return overpassStatus();
      default: return unknown(kind,"未確認");
    }
  }
  private Status facilityStatus() {
    // G09 v2 installs the database at filesDir/cb6_facilities.sqlite.
    // A readable file alone is not proof of renderer activation.
    File file=new File(context.getFilesDir(),"cb6_facilities.sqlite");
    if (!file.isFile())
      return unknown(Kind.FACILITY_SQLITE,"施設DB未配置／有効化・描画使用は未確認");
    try (SQLiteDatabase db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,
        SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS)) {
      try (Cursor check=db.rawQuery("PRAGMA quick_check(1)",null)) {
        if (!check.moveToFirst() || !"ok".equalsIgnoreCase(check.getString(0)))
          return new Status(Kind.FACILITY_SQLITE,Phase.ERROR,file.length(),file.length(),
              -1,file.lastModified(),"","施設DB整合性検査失敗","SQLite quick_check failed");
      }
      return new Status(Kind.FACILITY_SQLITE,Phase.UNKNOWN,file.length(),file.length(),
          -1,file.lastModified(),String.valueOf(db.getVersion()),
          "施設DB読取可能／有効化・描画使用の確認記録なし","");
    } catch(RuntimeException e) {
      return new Status(Kind.FACILITY_SQLITE,Phase.ERROR,file.length(),file.length(),
          -1,file.lastModified(),"","施設DB読取失敗",e.getClass().getSimpleName());
    }
  }
  private Status overpassStatus() {
    try {
      Cb6OverpassDiagnostics.Snapshot d=Cb6OverpassDiagnostics.read(context);
      if(!d.attempted) return unknown(Kind.OVERPASS,
          "Overpass診断フック未接続または通信記録なし／キャッシュ件数未確認");
      return new Status(Kind.OVERPASS,d.lastError.isEmpty()?Phase.UNKNOWN:Phase.ERROR,
          -1,-1,d.lastCount,d.lastSuccess,"",
          "最終通信試行: "+d.lastAttempt+"ms(epoch) ／ 最終成功時の取得件数（キャッシュ件数ではない）",
          d.lastError);
    } catch(RuntimeException e) {
      return new Status(Kind.OVERPASS,Phase.ERROR,-1,-1,-1,-1,"",
          "Overpass診断記録の読取失敗",e.getClass().getSimpleName());
    }
  }
  /** Actual CoMaps country records, not filesystem guesses. The aggregate does not
      claim that all of Hokkaido is downloaded. */
  private Status mapStatus() {
    try {
      List<CountryItem> items = new ArrayList<>();
      MapManager.nativeListItems(null, 0, 0, false, true, items);
      int done=0, progress=0, failed=0;
      long bytes=0;
      StringBuilder names=new StringBuilder();
      for (CountryItem item:items) {
        if (item.status==CountryItem.STATUS_DONE) {
          done++;
          if (item.size>0) bytes+=item.size;
          if (names.length()<180) {
            if (names.length()>0) names.append("、");
            names.append(item.name==null?item.id:item.name);
          }
        } else if(item.status==CountryItem.STATUS_PROGRESS ||
                  item.status==CountryItem.STATUS_APPLYING ||
                  item.status==CountryItem.STATUS_ENQUEUED) progress++;
        else if(item.status==CountryItem.STATUS_FAILED) failed++;
      }
      boolean downloading=MapManager.nativeIsDownloading();
      String detail="保存済み地図: "+done+"件"+
          " ／ 取得中・待機: "+progress+"件 ／ 失敗: "+failed+"件"+
          (names.length()>0?" ／ "+names:"")+
          " ／ 北海道全域の取得完了は未判定";
      return new Status(Kind.MWM,downloading?Phase.DOWNLOADING:
          failed>0?Phase.ERROR:done>0?Phase.DOWNLOADED:Phase.UNKNOWN,
          -1,-1,done,-1,"",detail,failed>0?"地図取得失敗あり":"");
    } catch (RuntimeException | LinkageError e) {
      return new Status(Kind.MWM,Phase.ERROR,-1,-1,-1,-1,"",
          "CoMaps地図状態APIの取得失敗",e.getClass().getSimpleName());
    }
  }

  private Status signalStatus() {
    try {
      String name=context.getSharedPreferences("cb6_signal_db",Context.MODE_PRIVATE)
          .getString("active_file",null);
      if(name==null) return new Status(Kind.SIGNAL_SQLITE,Phase.NOT_INSTALLED,-1,-1,-1,-1,"","有効化されたSQLiteなし","");
      if(!name.matches("signals-[0-9a-f]{64}\\.sqlite"))
        return new Status(Kind.SIGNAL_SQLITE,Phase.ERROR,-1,-1,-1,-1,"","有効DB名が不正","Invalid active filename");
      File f=new File(new File(context.getFilesDir(),"cb6-signal-db"),name);
      if(!f.isFile()) return new Status(Kind.SIGNAL_SQLITE,Phase.ERROR,-1,-1,-1,-1,"","使用中DBが見つかりません","Missing active file");
      // Read-only metadata inspection. Do not claim ACTIVE/VERIFIED: the full
      // SQLiteSignalProvider.validate() and renderer consumption are separate.
      try (SQLiteDatabase db=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,
          SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS)) {
        int userVersion=db.getVersion();
        long count;
        try(Cursor c=db.rawQuery("SELECT count(*) FROM signals",null)) {
          if(!c.moveToFirst()) throw new IllegalStateException("signals count unavailable");
          count=c.getLong(0);
        }
        String version="";
        try(Cursor c=db.rawQuery("SELECT dataset_version FROM package_info LIMIT 1",null)) {
          if(c.moveToFirst() && !c.isNull(0)) version=c.getString(0);
        }
        return new Status(Kind.SIGNAL_SQLITE,Phase.UNKNOWN,f.length(),f.length(),count,
            f.lastModified(),version,"DB参照あり ／ schema="+userVersion+
            " ／ 件数・版は読取済み ／ 全件検証と描画使用状態は未確認","");
      } catch(Exception ex) {
        return new Status(Kind.SIGNAL_SQLITE,Phase.ERROR,f.length(),f.length(),-1,
            f.lastModified(),"","DBメタデータ読取失敗（旧DBは変更しません）",
            ex.getClass().getSimpleName());
      }
    } catch (RuntimeException e) {
      return new Status(Kind.SIGNAL_SQLITE,Phase.ERROR,-1,-1,-1,-1,"","信号機DBの状態取得失敗",e.getClass().getSimpleName());
    }
  }
}
