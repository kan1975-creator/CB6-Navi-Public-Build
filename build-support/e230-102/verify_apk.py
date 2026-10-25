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
 assert b'highway|traffic_signals' in z.read('assets/types.txt')
 assert len([n for n in names if n.startswith('assets/symbols/') and n.endswith('.sdf') and b'cb6-signal-' in z.read(n)])==12
 (out/'apk_contents.txt').write_text('\n'.join(names))
(out/'APK_RESULT.json').write_text(json.dumps({'apk':apk.name,'bytes':apk.stat().st_size,'sha256':hashlib.file_digest(apk.open('rb'),'sha256').hexdigest(),'certificate_sha256':cert,'build_exit':0,'device_acceptance':'NOT_RUN','adoption':'STOP'},indent=2))
shutil.copy2(apk,out/apk.name)
