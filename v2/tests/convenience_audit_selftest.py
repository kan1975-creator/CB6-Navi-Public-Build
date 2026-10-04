#!/usr/bin/env python3
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "v2/audits/audit_convenience.py"
FILES = [
    "v2/poi/native/convenience_mwm_collector.hpp",
    "v2/poi/native/convenience_mwm_collector.cpp",
    "v2/poi/native/convenience_brand_classifier.cpp",
    "v2/poi/apply_convenience_mwm_diagnostic.py",
    "v2/poi/apply_convenience_brand_render.py",
]

def run(root):
    p = subprocess.run(["python3", str(root / "v2/audits/audit_convenience.py")],
                       cwd=root, text=True, capture_output=True)
    return p.returncode, p.stdout + p.stderr

def stage(tmp):
    for rel in FILES + ["v2/audits/audit_convenience.py"]:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text((ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")

with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    stage(tmp)
    rc, out = run(tmp)
    if rc != 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: valid fixture rejected\n" + out)

    collector = tmp / "v2/poi/native/convenience_mwm_collector.cpp"
    original = collector.read_text(encoding="utf-8")

    collector.write_text(original.replace("dataSource.ForEachInRect(", "dataSource.NotForEachInRect("), encoding="utf-8")
    rc, _ = run(tmp)
    if rc == 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: missing MWM iteration was accepted")

    collector.write_text(original + '\n// overpass-api.de must be rejected\n', encoding="utf-8")
    rc, _ = run(tmp)
    if rc == 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: forbidden network ownership was accepted")

    collector.write_text(original + '\n// nativeSetCb6DrivingMarks must be rejected\n', encoding="utf-8")
    rc, _ = run(tmp)
    if rc == 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: signal/UserMark ownership crossing was accepted")


    final = tmp / "v2/poi/apply_convenience_brand_render.py"
    final_original = final.read_text(encoding="utf-8")
    final.write_text(final_original.replace("UserMark::Type::CONVENIENCE", "UserMark::Type::DEBUG_MARK"), encoding="utf-8")
    rc, _ = run(tmp)
    if rc == 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: non-dedicated renderer group was accepted")
    final.write_text(final_original + "\n# nativeSetCb6DrivingMarks forbidden crossing\n", encoding="utf-8")
    rc, _ = run(tmp)
    if rc == 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: final renderer signal crossing was accepted")

    final.write_text(final_original + "\n# CB6_SIGNAL outside coexistence anchor must be rejected\n", encoding="utf-8")
    rc, _ = run(tmp)
    if rc == 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: extra Signal dependency was accepted")

    final.write_text(final_original.replace(
        'signal_old = "    TRAFFIC_LIGHT,\\n    CB6_SIGNAL,\\n    USER_MARK_TYPES_COUNT,"',
        'signal_old = "    TRAFFIC_LIGHT,\\n    USER_MARK_TYPES_COUNT,"'), encoding="utf-8")
    rc, _ = run(tmp)
    if rc == 0:
        raise SystemExit("CB6 CONVENIENCE AUDIT SELFTEST FAIL: missing coexistence anchor was accepted")

print("CB6 CONVENIENCE AUDIT SELFTEST PASS: valid path accepted and acquisition/render ownership mutations rejected")
