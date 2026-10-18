package app.organicmaps.cb6.signals;

import android.content.Context;

/** Read-only viewport gateway: never opens a network connection or falls back to Overpass. */
final class OfflineSignalProvider
{
  private final OfflineSignalStore store;
  OfflineSignalProvider(Context context) { store=new OfflineSignalStore(context); }
  void bootstrapIfNeeded() throws Exception { store.bootstrapIfNeeded(); }
  SignalSnapshot loadViewport(double south, double west, double north, double east) throws Exception
  {
    return store.query(south,west,north,east);
  }
  int importOwnerSignedZip(java.io.InputStream archive) throws Exception
  {
    return store.install(archive,false);
  }
  boolean isOwnerKeyConfigured() { return OfflineSignalStore.configured(); }
}
