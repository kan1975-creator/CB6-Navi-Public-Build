#!/usr/bin/env python3
"""CB6 final convenience renderer patch scaffold.

Authority: installed MWM DataSource collector + deterministic brand classifier.
This patch must remain independent from nativeSetCb6DrivingMarks and all signal ownership.
"""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()

# Implementation is intentionally fail-closed until the dedicated renderer and symbol
# injection are completed and audited. The feature gate may be implementation-enabled,
# but an APK workflow must not treat this scaffold as final rendering evidence.
raise SystemExit("CB6 convenience final renderer not implemented yet: dedicated signal-independent renderer required")
