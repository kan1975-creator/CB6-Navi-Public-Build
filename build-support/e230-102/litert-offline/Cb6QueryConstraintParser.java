package jp.cb6.search;

import java.util.*;
import java.util.regex.*;
public final class Cb6QueryConstraintParser {
 private final Cb6CategoryDictionary dict;
 public Cb6QueryConstraintParser(Cb6CategoryDictionary d){dict=d;}
 public static final class Result {
  final BitSet required=new BitSet(), excluded=new BitSet(); boolean only, review;
  public BitSet required(){return (BitSet)required.clone();} public BitSet excluded(){return (BitSet)excluded.clone();}
  public boolean requiresReview(){return review;} public boolean limited(){return only;}
 }
 private static final Pattern CLAUSE=Pattern.compile("^(.+?)(?:は|を|が)?(いらない|不要|除外|なし|以外|ではなく|じゃなく|だけ|のみ|必須|お願い|探して|も必要|必要|取消|取り消し)$");
 private static final Pattern CONTROL=Pattern.compile("いらな|不要|除外|なし|以外|なく|だけ|のみ|必須|必要|取消|取り消|訂正|やめ|ない|ません|違う|代わり|限定|以外|除く|キャンセル|じゃなく|ではなく");
 public Result parse(String input){Result out=new Result(); String s=Cb6CategoryDictionary.norm(input); if(s.codePointCount(0,s.length())>128){out.review=true;return out;}
  s=s.replaceAll("(ではなく|じゃなく)(?=[^、。,.!！?？\\s])","$1、");
  for(String raw:s.split("[、。,.!！?？\\n]+")){String c=raw.trim().replaceFirst("(?:してください|して下さい|ください|下さい|です|だよ|よ)$", "").trim(); if(c.isEmpty())continue;
   if(c.matches(".*(?:ではない|わけでは|なくても|なくていい|以外なら|以外も|以外は|どちらか|または|もしくは|かどうか|不要では|いらないことは|除外しない).*")){out.review=true;continue;}
   boolean correction=c.startsWith("訂正:")||c.startsWith("訂正："); if(correction)c=c.substring(3).trim();
   Matcher m=CLAUSE.matcher(c); String name=c,op=""; if(m.matches()){name=m.group(1);op=m.group(2);}
   BitSet b=new BitSet(); boolean known=true; for(String n:name.split("(?:と|および|及び|・)")){BitSet x=dict.exact(n);if(x.cardinality()!=1){known=false;break;}b.or(x);}
   if(!known){if(correction||CONTROL.matcher(c).find())out.review=true;continue;}
   if(correction){out.required.clear();out.excluded.clear();out.only=false;}
   if(op.equals("取消")||op.equals("取り消し")){out.required.andNot(b);out.excluded.andNot(b);if(out.only&&out.required.isEmpty())out.review=true;continue;}
   if(Arrays.asList("いらない","不要","除外","なし","以外","ではなく","じゃなく").contains(op))out.excluded.or(b);
   else {boolean limited=op.equals("だけ")||op.equals("のみ"); if((limited&&!out.required.isEmpty()&&!out.required.equals(b))||(out.only&&!out.required.equals(b)))out.review=true; out.required.or(b);if(limited)out.only=true;}
  }
  if(out.required.intersects(out.excluded))out.review=true;return out;
 }
}
