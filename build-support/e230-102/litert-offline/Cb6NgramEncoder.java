package jp.cb6.search;

import java.text.Normalizer;
import java.nio.charset.StandardCharsets;
public final class Cb6NgramEncoder {
 public static int[] encode(String input) {
  int[] cp=Normalizer.normalize(input,Normalizer.Form.NFKC).codePoints().limit(128).toArray();
  int[] result=new int[378]; int k=0;
  for(int n=2;n<=4;n++) for(int i=0;i+n<=cp.length;i++) {
   int h=0x811c9dc5;
   for(byte b:new String(cp,i,n).getBytes(StandardCharsets.UTF_8)) h=(h^(b&255))*0x01000193;
   result[k++]=1+(int)(Integer.toUnsignedLong(h)%65535);
  }
  return result;
 }
}
