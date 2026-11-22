#!/usr/bin/env python3
# Isolated G09 integration after convenience stage.
from pathlib import Path
import sys
if len(sys.argv) != 2: raise SystemExit('usage: apply_g09_sqlite_single_source.py <comaps-root>')
root=Path(sys.argv[1]).resolve()
base=Path(__file__).resolve().parent
activity=root/'android/app/src/main/java/app/organicmaps/MwmActivity.java'
target=root/'android/app/src/main/java/app/organicmaps/cb6/facilities'
if not activity.is_file(): raise SystemExit('STOP: MwmActivity missing')
if any((target/x).exists() for x in ('SQLiteFacilityRepository.java','Cb6FacilityDbInstaller.java','Cb6FacilityDbDownload.java')):
    raise SystemExit('STOP: G09 destination occupied')
s=activity.read_text()
anchor='''    if (cb6ConvenienceAlreadyCovered(lat, lon, scale)) return;
    final int generation = mCb6ConvenienceGeneration.get();
'''
replacement='''    if (cb6ConvenienceAlreadyCovered(lat, lon, scale)) return;
    final int generation = mCb6ConvenienceGeneration.get();
    // SQLite is the sole source once an installed facility database is available.
    // Until then the original MWM path below is retained unchanged.
    final java.io.File g09Db = new java.io.File(getFilesDir(), "cb6_facilities.sqlite");
    if (mCb6G09SqliteSelected)
    {
      try
      {
        mCb6ConvenienceTransform.execute(() ->
        {
          try
          {
            final app.organicmaps.cb6.facilities.SQLiteFacilityRepository.Marks marks =
                app.organicmaps.cb6.facilities.SQLiteFacilityRepository.query(
                    g09Db, Math.max(-90.0, lat - 0.04), Math.min(90.0, lat + 0.04),
                    Math.max(-180.0, lon - 0.06), Math.min(180.0, lon + 0.06));
            mCb6ConvenienceHandler.post(() ->
            {
              if (mCb6ConveniencePaused || generation != mCb6ConvenienceGeneration.get() ||
                  !cb6ConvenienceRenderingActive()) return;
              Framework.nativeSetCb6ConvenienceMarks(marks.lats, marks.lons, marks.kinds);
              if (marks.lats.length > 0) cb6ConvenienceRememberCovered(lat, lon, scale);
            });
          }
          catch (android.database.sqlite.SQLiteException | IllegalStateException e)
          {
            android.util.Log.e("CB6-G09", "SQLite query failed; not switching to MWM", e);
          }
        });
      }
      catch (java.util.concurrent.RejectedExecutionException ignored) {}
      return;
    }
'''
# Install bundled DB on the existing worker; never do I/O on main thread.
resume='''    mCb6ConveniencePaused = false;
    Framework.nativeSetCb6ConvenienceMarks(new double[0], new double[0], new int[0]);
    mCb6ConvenienceCovered.clear();
    app.organicmaps.sdk.MapView.setCb6OnGestureEnd(mCb6ConvenienceGestureEnd);
'''
new_resume='''    mCb6ConveniencePaused = false;
    // Freeze source for the Activity lifetime: no mid-session MWM->SQLite
    // transition while native convenience marks are append-only.
    if (!mCb6G09SourceSelected)
    {
      mCb6G09SourceSelected = true;
      mCb6G09SqliteSelected =
          app.organicmaps.cb6.facilities.Cb6FacilityDbDownload.valid(
              new java.io.File(getFilesDir(), "cb6_facilities.sqlite"));
      mCb6ConvenienceTransform.execute(() ->
      {
        // Bundled DB is optional; never overwrite a downloaded database.
        app.organicmaps.cb6.facilities.Cb6FacilityDbInstaller.ensureInstalled(this);
        // Download is optional and requires a trusted HTTPS URL + SHA-256
        // supplied in the APK asset. Newly installed DB activates next launch.
        app.organicmaps.cb6.facilities.Cb6FacilityDbDownload.downloadConfigured(this);
      });
    }
    Framework.nativeSetCb6ConvenienceMarks(new double[0], new double[0], new int[0]);
    mCb6ConvenienceCovered.clear();
    app.organicmaps.sdk.MapView.setCb6OnGestureEnd(mCb6ConvenienceGestureEnd);
'''
source_fields = """  private boolean mCb6G09SourceSelected = false;
  private boolean mCb6G09SqliteSelected = false;
"""
field_anchor = "  private boolean mCb6ConveniencePaused = true;\n"
if s.count(field_anchor) != 1: raise SystemExit('STOP: source fields anchor missing')
s = s.replace(field_anchor, field_anchor + source_fields, 1)
for old in (anchor,resume):
 if s.count(old)!=1: raise SystemExit('STOP: expected source anchor not unique')
s=s.replace(anchor,replacement,1).replace(resume,new_resume,1)
for filename in ('SQLiteFacilityRepository.java','Cb6FacilityDbInstaller.java','Cb6FacilityDbDownload.java'):
 if not (base/filename).is_file(): raise SystemExit('STOP: G09 source missing '+filename)
target.mkdir(parents=True,exist_ok=True)
for filename in ('SQLiteFacilityRepository.java','Cb6FacilityDbInstaller.java','Cb6FacilityDbDownload.java'):
 (target/filename).write_bytes((base/filename).read_bytes())
activity.write_text(s)
print('G09_SQLITE_SINGLE_SOURCE_APPLIED: 1 Activity + 3 new Java files; JNI/POI/signal untouched')
