package jp.cb6.search;

import java.io.*;
import java.text.Normalizer;
import java.util.*;
public final class Cb6CategoryDictionary {
 public static final int COUNT=1083;
 private final Map<String,Integer> ids=new HashMap<>();
 private final Map<String,BitSet> aliases=new HashMap<>();
 public Cb6CategoryDictionary(Reader source, Reader aliasSource) throws IOException {
  BufferedReader r=new BufferedReader(source); String line; int i=0;
  while((line=r.readLine())!=null){String[] p=line.split("\t",-1); if(p.length!=2||p[0].isEmpty()||p[1].isEmpty()||ids.put(p[0],i++)!=null)throw new IOException("invalid category");}
  if(i!=COUNT)throw new IOException("category count");
  r=new BufferedReader(aliasSource); while((line=r.readLine())!=null){String[] p=line.split("\t",-1); if(p.length!=2||!ids.containsKey(p[0])||norm(p[1]).isEmpty())throw new IOException("invalid alias"); aliases.computeIfAbsent(norm(p[1]),k->new BitSet(COUNT)).set(ids.get(p[0]));}
 }
 static String norm(String s){return Normalizer.normalize(s,Normalizer.Form.NFKC).toLowerCase(Locale.ROOT).trim();}
 public static Cb6CategoryDictionary verified(byte[] bytes, Reader aliases) throws IOException {
  try { java.security.MessageDigest d=java.security.MessageDigest.getInstance("SHA-256"); StringBuilder hex=new StringBuilder(); for(byte b:d.digest(bytes))hex.append(String.format(Locale.ROOT,"%02x",b&255)); if(!hex.toString().equals("e394297af46b87b99f8da37ceab5d9e578633c0e0a29b179d8e82a2d96401d9c"))throw new IOException("category SHA mismatch"); } catch(java.security.NoSuchAlgorithmException e){throw new IOException(e);}
  return new Cb6CategoryDictionary(new InputStreamReader(new ByteArrayInputStream(bytes),java.nio.charset.StandardCharsets.UTF_8),aliases);
 }
 public BitSet exact(String s){BitSet b=aliases.get(norm(s));return b==null?new BitSet(COUNT):(BitSet)b.clone();}
}
