package jp.cb6.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.tensorflow.lite.Interpreter;
import org.tensorflow.lite.DataType;
/** Worker-confined inference core; caller owns scheduling and lifecycle. */
public final class Cb6LiteRtSearch implements AutoCloseable {
 private final Interpreter interpreter;
 private final Cb6QueryConstraintParser parser;
 public Cb6LiteRtSearch(File model, byte[] categories, Reader terms) throws IOException {
  BufferedReader r=new BufferedReader(terms);
  if(!"id\tterm".equals(r.readLine()))throw new IOException("alias header");
  StringBuilder aliases=new StringBuilder(); String line; Set<String> ids=new HashSet<>();
  while((line=r.readLine())!=null){String[] p=line.split("\t",-1);if(p.length!=2||!ids.add(p[0]))throw new IOException("alias row");aliases.append(line).append('\n');}
  if(ids.size()!=1083)throw new IOException("alias count");
  parser=new Cb6QueryConstraintParser(Cb6CategoryDictionary.verified(categories,new StringReader(aliases.toString())));
  Interpreter i=new Interpreter(model,new Interpreter.Options().setNumThreads(1).setUseNNAPI(false));
  try {
   if(i.getInputTensorCount()!=1||i.getOutputTensorCount()!=1||!Arrays.equals(i.getInputTensor(0).shape(),new int[]{1,378})||!Arrays.equals(i.getOutputTensor(0).shape(),new int[]{1,1083})||i.getInputTensor(0).dataType()!=DataType.INT32||i.getOutputTensor(0).dataType()!=DataType.FLOAT32)throw new IOException("tensor contract");
  }catch(IOException|RuntimeException e){i.close();throw e;}
  interpreter=i;
 }
 public Cb6CategoryResolver.Decision search(String query){
  Cb6QueryConstraintParser.Result c=parser.parse(query);
  float[][] scores=new float[1][1083];
  if(!c.requiresReview())interpreter.run(new int[][]{Cb6NgramEncoder.encode(query)},scores);
  return new Cb6CategoryResolver().resolve(scores[0],0.925f,c);
 }
 public void close(){interpreter.close();}
}
