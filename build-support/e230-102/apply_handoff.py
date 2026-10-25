"""Restore the exact approved Work payload; never reimplement signal logic."""
import hashlib,io,json,shutil,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
support=Path(__file__).resolve().parent
repo=Path(sys.argv[1]).resolve()
manifest=json.loads((support/'manifest.json').read_text())
parts=[]
for item in manifest['parts']:
 b=(support/item['name']).read_bytes()
 assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['name']
 parts.append(b)
b=b''.join(parts)
assert len(b)==manifest['bytes'] and hashlib.sha256(b).hexdigest()==manifest['sha256']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()=='7113ccb5f086183f8884b2aa4e58c987466b6704'
evidence=support/'out';evidence.mkdir(exist_ok=True)
(evidence/'handoff.sha256').write_text(manifest['sha256']+'  '+manifest['filename']+'\n')
with zipfile.ZipFile(io.BytesIO(b)) as outer:
 with zipfile.ZipFile(io.BytesIO(outer.read('source/CB6_E230_IMPLEMENTED_APK_UNGENERATED.zip'))) as src:
  patch=src.read('SOURCE_FROM_FIXED_COMAPS.patch')
  subprocess.run(['git','apply','--check','-'],cwd=repo,input=patch,check=True)
  subprocess.run(['git','apply','-'],cwd=repo,input=patch,check=True)
  for rel,sha in json.loads(src.read('SOURCE_SHA256.json')).items():
   assert hashlib.sha256((repo/rel).read_bytes()).hexdigest()==sha,rel
  generated=[]
  for name in src.namelist():
   if name.startswith('generated_overlay/') and not name.endswith('/'):
    rel=PurePosixPath(name).relative_to('generated_overlay')
    assert not rel.is_absolute() and '..' not in rel.parts
    target=repo/str(rel)
    assert target.resolve().is_relative_to(repo),name
    target.parent.mkdir(parents=True,exist_ok=True)
    data=src.read(name);target.write_bytes(data)
    generated.append({'path':str(rel),'sha256':hashlib.sha256(data).hexdigest()})
  (evidence/'generated_assets.json').write_text(json.dumps(generated,indent=2))
  for name in ['SOURCE_SHA256.json','STATUS.json','NATIVE_IDENTIFICATION.json','README_JA.txt']:
   (evidence/('inherited_'+name)).write_bytes(src.read(name))
# Reject production signing inputs; release variant deliberately uses upstream debug signing.
for n in ['secure.properties.release','secure.properties.test','google-play.json','huawei-appgallery.json']:
 assert not (repo/'android/app'/n).exists(),n
(evidence/'application.txt').write_text('Fixed source patch applied. Source manifest matched. Generated assets copied from approved ZIP. Existing 53 tests and native PASS inherited; no tests run.\n')
