package jp.cb6.search;

import java.nio.*;
import java.util.*;
import java.util.function.BooleanSupplier;
/** Existing little-endian category postings; no regeneration. */
public final class Cb6PlaceIndex {
 private static final int N=1083, BASE=(N+1)*4;
 private final ByteBuffer data;
 public Cb6PlaceIndex(byte[] bytes){
  if(bytes.length<BASE)throw new IllegalArgumentException("index header");
  data=ByteBuffer.wrap(bytes).asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);
  if(offset(0)!=0 || BASE+12L*offset(N)!=bytes.length)throw new IllegalArgumentException("index size");
  for(int c=0;c<N;c++){if(offset(c)<0||offset(c)>offset(c+1)||offset(c+1)>offset(N))throw new IllegalArgumentException("offset");int prev=-1;for(int i=offset(c);i<offset(c+1);i++){int id=field(i,0);if(id<=prev)throw new IllegalArgumentException("posting order");prev=id;}}
 }
 private int offset(int c){return data.getInt(c*4);}
 private int field(int i,int f){return data.getInt(BASE+12*i+4*f);}
 private boolean contains(int c,int id){int lo=offset(c),hi=offset(c+1);while(lo<hi){int m=(lo+hi)>>>1;if(field(m,0)<id)lo=m+1;else hi=m;}return lo<offset(c+1)&&field(lo,0)==id;}
 public int[] nearest(BitSet selected,BitSet excluded,double lat,double lon,int limit,BooleanSupplier canceled){
  if(selected.length()>N||excluded.length()>N||limit<1||limit>32||!Double.isFinite(lat)||!Double.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180)throw new IllegalArgumentException("query");
  Comparator<Hit> cmp=Comparator.comparingDouble((Hit h)->h.d).thenComparingInt(h->h.id);PriorityQueue<Hit> q=new PriorityQueue<>(limit,cmp.reversed());Set<Integer> active=new HashSet<>();double scale=Math.cos(Math.toRadians(lat));
  for(int c=selected.nextSetBit(0);c>=0;c=selected.nextSetBit(c+1)){for(int i=offset(c);i<offset(c+1);i++){if(canceled.getAsBoolean())throw new java.util.concurrent.CancellationException();int id=field(i,0);if(active.contains(id))continue;boolean reject=false;for(int e=excluded.nextSetBit(0);e>=0;e=excluded.nextSetBit(e+1))if(contains(e,id)){reject=true;break;}if(reject)continue;double dy=field(i,1)*1e-6-lat,dx=(field(i,2)*1e-6-lon)*scale;Hit h=new Hit(id,dx*dx+dy*dy);if(q.size()==limit&&cmp.compare(h,q.peek())>=0)continue;q.add(h);active.add(id);if(q.size()>limit)active.remove(q.remove().id);}}
  return q.stream().sorted(cmp).mapToInt(h->h.id).toArray();
 }
 private static final class Hit{final int id;final double d;Hit(int id,double d){this.id=id;this.d=d;}}
}
