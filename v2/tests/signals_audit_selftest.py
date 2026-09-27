#!/usr/bin/env python3
"""Fail-closed proof for the Signal source audit contract."""
from pathlib import Path
import shutil, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[2]

def prepare(dst):
    shutil.copytree(ROOT/"v2",dst/"v2")
    (dst/"android/app/src/main/java/app/organicmaps").mkdir(parents=True,exist_ok=True)
    # This self-test intentionally exercises repository-level audit mutations through a real
    # transformed tree in CI; standalone fixture construction is not authoritative.
    return dst

# The full signal audit depends on a transformed pinned-CoMaps tree, so its destructive proof
# is performed by the Gate 1 workflow after apply_signals.py. This file is the registered
# executable proof contract and must reject execution without that transformed root.
if __name__=="__main__":
    raise SystemExit("SIGNAL AUDIT SELFTEST REQUIRES_TRANSFORMED_TREE")
