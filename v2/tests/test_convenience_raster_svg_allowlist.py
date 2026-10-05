#!/usr/bin/env python3
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SOURCE=ROOT/"v2/poi/apply_convenience_brand_render.py"
EXPECTED={"cb6-seven.png","cb6-familymart.png","cb6-lawson.png","cb6-seicomart.png","cb6-ministop.png","cb6-mybasket.png"}
def load_policy():
 tree=ast.parse(SOURCE.read_text()); selected=[]
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CB6_DIRECT_PNG_ALLOWLIST" for t in node.targets): selected.append(node)
  elif isinstance(node,ast.FunctionDef) and node.name=="cb6_extract_approved_png": selected.append(node)
 ns={}; exec(compile(ast.Module(body=selected,type_ignores=[]),str(SOURCE),"exec"),ns); return ns["CB6_DIRECT_PNG_ALLOWLIST"],ns["cb6_extract_approved_png"]
def test_allowlist_is_exactly_six_png_files():
 allowlist,_=load_policy(); assert set(allowlist)==EXPECTED and len(allowlist)==6
def test_exact_allowed_source_extracts_png_bytes_unchanged():
 _,extract=load_policy(); payload="iVBORw0KGgo="
 for png in EXPECTED:
  name,raw=extract(png[:-4]+".svg",'<svg><image href="data:image/png;base64,'+payload+'"/></svg>'); assert name==png; assert raw==b"\x89PNG\r\n\x1a\n"
def test_non_allowlisted_png_rejected():
 _,extract=load_policy()
 try: extract("cb6-daily.svg",'<svg><image href="data:image/png;base64,iVBORw0KGgo="/></svg>')
 except ValueError: pass
 else: raise AssertionError("non-allowlisted direct PNG accepted")
def test_near_match_filename_rejected_fail_closed():
 _,extract=load_policy(); svg='<svg><image href="data:image/png;base64,iVBORw0KGgo="/></svg>'
 for name in ("CB6-seven.svg","cb6-seven-copy.svg","cb6-seven.svg.bak","path/cb6-seven.svg"):
  try: extract(name,svg)
  except ValueError: continue
  raise AssertionError("near-match filename accepted: "+name)
def test_multiple_or_non_png_payload_rejected():
 _,extract=load_policy()
 for svg in ('<svg><image href="data:image/png;base64,QUJD"/></svg>','<svg><image href="data:image/png;base64,iVBORw0KGgo="/><image href="data:image/png;base64,iVBORw0KGgo="/></svg>'):
  try: extract("cb6-seven.svg",svg)
  except ValueError: continue
  raise AssertionError("invalid PNG source accepted")
if __name__=="__main__":
 for test in (test_allowlist_is_exactly_six_png_files,test_exact_allowed_source_extracts_png_bytes_unchanged,test_non_allowlisted_png_rejected,test_near_match_filename_rejected_fail_closed,test_multiple_or_non_png_payload_rejected): test(); print("PASS",test.__name__)
