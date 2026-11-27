package jp.cb6.search;

import java.util.*;
public final class Cb6CategoryResolver {
 public static final class Decision {private final BitSet selected, excluded; public final boolean review; Decision(BitSet b,boolean r,BitSet e){selected=(BitSet)b.clone();excluded=(BitSet)e.clone();review=r;} public BitSet excluded(){return (BitSet)excluded.clone();} public BitSet selected(){return (BitSet)selected.clone();}}
 public Decision resolve(float[] scores,float threshold,Cb6QueryConstraintParser.Result c){BitSet b=new BitSet();if(c.requiresReview()||scores.length!=Cb6CategoryDictionary.COUNT||!Float.isFinite(threshold)||threshold<=0||threshold>1)return new Decision(b,true,c.excluded());
  for(float v:scores)if(!Float.isFinite(v)||v<0||v>1)return new Decision(b,true,c.excluded());
  if(!c.limited())for(int i=0;i<scores.length;i++)if(scores[i]>=threshold)b.set(i);
  b.or(c.required());b.andNot(c.excluded());return new Decision(b,b.isEmpty(),c.excluded());
 }
}
