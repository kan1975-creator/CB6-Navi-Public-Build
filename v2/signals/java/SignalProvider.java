package app.organicmaps.cb6.signals;

/** Narrow acquisition boundary. Implementations execute off the main thread. */
public interface SignalProvider
{
  SignalSnapshot load(double lat, double lon) throws Exception;
}
