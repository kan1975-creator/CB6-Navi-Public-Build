from pathlib import Path
import hashlib, shutil, sys, subprocess
HERE=Path(__file__).resolve().parent
ROOT=Path(sys.argv[1]).resolve()
APP=ROOT/'android/app'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):
    if s.count(a)!=1: raise ValueError('anchor: '+a)
    return s.replace(a,b,1)
def main():
    for n,h in EXPECTED.items():
        if digest(HERE/n)!=h: raise ValueError(n)
    places=HERE.parent/'ruri-offline/places.bin'
    if digest(places)!='f85101c3ac68484f7ff973108af89b1557fe4c962db7368e1ca7d52c91af1d54': raise ValueError('places.bin')
    patch = HERE / 'ai-only.patch'
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=ROOT, check=True)
    gradle=APP/'build.gradle'; g=gradle.read_text()
    g=replace(g,'\ndependencies {','\ndependencies {\n    implementation files("libs/litert-1.4.2.aar", "libs/litert-api-1.4.2.aar")')
    g=replace(g,'\n  defaultConfig {','\n  defaultConfig {\n    ndk { abiFilters "arm64-v8a" }')
    assets=APP/'src/main/assets/cb6_litert'; libs=APP/'libs'; java=APP/'src/main/java/jp/cb6/search'
    copies=[(HERE/n,assets/n) for n in ['fg_model.tflite','categories.tsv','all_label_terms.tsv']]+[(places,assets/'places.bin')]+[(HERE/n,libs/n) for n in ['litert-1.4.2.aar','litert-api-1.4.2.aar']]+[(f,java/f.name) for f in HERE.glob('*.java')]
    for _,dst in copies:
        if dst.exists(): raise FileExistsError(dst)
    if '--check' in sys.argv: return
    for src,dst in copies:
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
    subprocess.run(['git', 'apply', str(patch)], cwd=ROOT, check=True)
    gradle.write_text(g)

EXPECTED = {'litert-1.4.2.pom': '9528ce669b5bb545a03cd14d92f429064af04a644f2cd8e306e7705e8bf40a30', 'Cb6NgramEncoder.java': '99f1d7f9345f65e6fcae968dc53a6f12b554bd1a372e3946f8ddf612ee1f7b95', 'Cb6LiteRtController.java': 'eceaae693a2e245d33a258f62ebed66894f7b670a6fdb36eb52a4cfdefd43e66', 'litert-api-1.4.2.pom': 'da9af6af75d05c7af53571cf45833fdbd80271a99306b397090dac199c38c0d8', 'Cb6PlaceIndex.java': '9d32fe78bd42495b46d6b76d435d57a1ae9f4da414dd352277da204d18082118', 'Cb6CategoryDictionary.java': 'bc0abb4b06e50367f2f17373dc092f4234ed4fb6934025faddf8d04cd84519c4', 'litert-api-1.4.2.aar': '66c2ba8086bd5cbf89bec2bd81c3de6c1a852312829cd55bc30c9dd26ffa357c', 'Cb6CategoryResolver.java': 'b79bd13a5891ed894cf683cc103386bc1f5022d484ae10b58872240a653d9572', 'all_label_terms.tsv': '968aeb7488126db7e0125b4e51870b2e9252ef974e075300c6a00985eff4a428', 'litert-1.4.2.aar': '9b02cdf9db0a698b341b59e75c54ab8221d6304577cc43830d01024caf1fca74', 'Cb6SqliteLookup.java': '7a14c6e76d8123f1032a87a23977694766312e3b557171ba0c286768af342b50', 'fg_model.tflite': 'aa7baf1680aa70aef245eb4f57ac19b908e4137f5eebf82b249f88b6f3a62de9', 'Cb6QueryConstraintParser.java': '70a5270f67878a0e5830383b987314b7357179ae6437156c43fd74375d121da3', 'Cb6LiteRtSearch.java': 'a2861b056bf25940fcdde21916f466be937c8843f8dc1b489f19323c7e41a926', 'categories.tsv': 'e394297af46b87b99f8da37ceab5d9e578633c0e0a29b179d8e82a2d96401d9c'}
if __name__ == "__main__": main()
