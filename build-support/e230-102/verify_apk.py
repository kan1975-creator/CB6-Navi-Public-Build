import hashlib,json,os,re,subprocess,sys,zipfile,shutil
from pathlib import Path
repo=Path(sys.argv[1]);out=Path(sys.argv[2]);bt=Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0'
assert (out/'build.exit').read_text().strip()=='0'
assert 'BUILD SUCCESSFUL' in (out/'build.log').read_text()
apks=list((repo/'android/app/build/outputs/apk/web/release').glob('*.apk'))
assert len(apks)==1,apks
apk=apks[0]
for cmd,name in [([str(bt/'apksigner'),'verify','--verbose','--print-certs',str(apk)],'signature.txt'),([str(bt/'aapt'),'dump','badging',str(apk)],'badging.txt')]:
 p=subprocess.run(cmd,capture_output=True,text=True);(out/name).write_text(p.stdout+p.stderr);p.check_returncode()
cert=re.search(r'Signer #1 certificate SHA-256 digest: (\w+)',(out/'signature.txt').read_text()).group(1)
assert cert=='0cccc7c349bcc0005f53aa1a58f42b1c8ec6a387513f7c33576390842eac301a',cert
with zipfile.ZipFile(apk) as z:
 assert z.testzip() is None
 names=z.namelist()
 assert {n.split('/')[1] for n in names if n.startswith('lib/') and n.endswith('.so')}=={'arm64-v8a'}
 for n in ['lib/arm64-v8a/liborganicmaps.so','assets/types.txt','assets/classificator.txt','assets/drules_proto_default_light.bin','assets/drules_proto_vehicle_light.bin']:assert n in names,n
 for asset in ('fg_model.tflite','categories.tsv','all_label_terms.tsv','places.bin'):
  name='assets/cb6_litert/'+asset
  staged=repo/'android/app/src/main'/name
  assert z.read(name)==staged.read_bytes(),name
 assert any(n.startswith('lib/arm64-v8a/') and ('tensorflowlite' in n or 'litert' in n.lower()) and n.endswith('.so') for n in names)
 print('APK verified: LiteRT model, categories, terms, places index and arm64 native library')
 assert b'highway|traffic_signals' in z.read('assets/types.txt')
 assert len([n for n in names if n.startswith('assets/symbols/') and n.endswith('.sdf') and b'cb6-signal-' in z.read(n)])==12
 # Verify that all six brands and their two reduced zoom variants are in the
 # actual APK symbol atlases, not merely in the source/Gradle build directory.
 brands=('seven','familymart','lawson','seicomart','ministop','mybasket')
 symbols=[f'cb6-{brand}{suffix}' for brand in brands for suffix in ('','-85','-50')]
 evidence=[]
 for density in ('mdpi','hdpi','xhdpi','6plus','xxhdpi','xxxhdpi'):
  for theme in ('light','dark'):
   for ext in ('sdf','png'):
    path=f'assets/symbols/{density}/{theme}/symbols.{ext}'
    assert path in names, f'APK_ATLAS_MISSING: {path}'
    source=repo/'data/symbols'/density/theme/f'symbols.{ext}'
    assert source.is_file(), f'SOURCE_ATLAS_MISSING: {source}'
    apk_bytes=z.read(path)
    source_bytes=source.read_bytes()
    assert apk_bytes==source_bytes, f'APK_ATLAS_DIFFERS_FROM_GENERATED: {path}'
    if ext=='sdf':
     import xml.etree.ElementTree as ET
     root=ET.fromstring(apk_bytes)
     registered={e.attrib['name'] for e in root.iter('symbol') if 'name' in e.attrib}
     missing=sorted(set(symbols)-registered)
     assert not missing, f'APK_BRAND_SYMBOLS_MISSING: {path}: {missing}'
    evidence.append({'path':path,'bytes':len(apk_bytes),'sha256':hashlib.sha256(apk_bytes).hexdigest()})
 (out/'CONVENIENCE_APK_ATLAS.json').write_text(json.dumps({'brands':list(brands),'symbol_names':symbols,'atlas_files':evidence,'status':'PASS'},indent=2))
 (out/'apk_contents.txt').write_text('\n'.join(names))
(out/'APK_RESULT.json').write_text(json.dumps({'apk':apk.name,'bytes':apk.stat().st_size,'sha256':hashlib.file_digest(apk.open('rb'),'sha256').hexdigest(),'certificate_sha256':cert,'build_exit':0,'device_acceptance':'NOT_RUN','adoption':'STOP'},indent=2))
shutil.copy2(apk,out/apk.name)

print((out/'APK_RESULT.json').read_text())
