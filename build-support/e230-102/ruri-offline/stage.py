"""Install the offline overlay after the existing Stage 7 and AI patches."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve()
APP = ROOT / "android/app"
ASSETS = APP / "src/main/assets/cb6_ruri"
LIB = APP / "libs/onnxruntime-android-1.22.0.aar"
SP = ROOT / "android/sdk/src/main/cpp/cb6_ruri/sentencepiece"
EXPECTED = {'NOTICES.txt': '97cc8aabbb2cfa8ad238382dfd2e70c85d0dc6e337068479e1220dcded2c860e', 'categories.f32': 'f9ba93a9ff756fb1ccf4b17310c2d89f9c2db45df12868eae5950905ff11709d', 'categories.tsv': 'e394297af46b87b99f8da37ceab5d9e578633c0e0a29b179d8e82a2d96401d9c', 'model_int8.onnx': 'bd07545fa4eb8e7765939536944da1138a7e61441d81633adfa1faf218df6bb1', 'onnxruntime-android-1.22.0.aar': '04a4617a9c797cf49225595e45b5546081cb34c86ac817581141577d3b7dbfe2', 'places.bin': 'f85101c3ac68484f7ff973108af89b1557fe4c962db7368e1ca7d52c91af1d54', 'ruri.patch': '2aae76687b2909fbe199a2aea443db532992f0bd5714c55b3b6ff3e0ff73292a', 'sentencepiece-v0.2.0.tar.gz': '7710982d3b438e790646f8be623f3bbe6af1e2f2619129d1f946d4070d26bc34', 'tokenizer.model': '008293028e1a9d9a1038d9b63d989a2319797dfeaa03f171093a57b33a3a8277'}
SOURCE = "sentencepiece-17d7580d6407802f85855d2cc9190634e2c95624"
ASSET_NAMES = ["model_int8.onnx", "tokenizer.model", "categories.tsv", "categories.f32", "places.bin", "NOTICES.txt"]

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def main():
    for name, expected in EXPECTED.items():
        if digest(HERE / name) != expected:
            raise ValueError("Unexpected file: " + name)
    for target in [ASSETS, LIB, SP]:
        if target.exists():
            raise FileExistsError(target)
    patch = ["git", "apply", "--whitespace=error"]
    subprocess.run([*patch, "--check", str(HERE / "ruri.patch")], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(dir=APP) as temp:
        staging = Path(temp)
        with tarfile.open(HERE / "sentencepiece-v0.2.0.tar.gz") as archive:
            archive.extractall(staging, filter="data")
        assets = staging / "assets"
        assets.mkdir()
        for name in ASSET_NAMES:
            shutil.copyfile(HERE / name, assets / name)
        shutil.copyfile(HERE / LIB.name, staging / LIB.name)
        source = staging / SOURCE
        if (source / "VERSION.txt").read_text().strip() != "0.2.0":
            raise ValueError("SentencePiece version")
        installed = []
        subprocess.run([*patch, str(HERE / "ruri.patch")], cwd=ROOT, check=True)
        try:
            for src, dst in [(source, SP), (assets, ASSETS), (staging / LIB.name, LIB)]:
                dst.parent.mkdir(parents=True, exist_ok=True)
                src.rename(dst)
                installed.append(dst)
        except BaseException:
            for path in reversed(installed):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            subprocess.run(["git", "apply", "-R", str(HERE / "ruri.patch")], cwd=ROOT, check=True)
            raise

if __name__ == "__main__":
    main()
