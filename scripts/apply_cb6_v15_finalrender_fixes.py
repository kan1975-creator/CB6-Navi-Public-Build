#!/usr/bin/env python3
from pathlib import Path
import re
import sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("comaps").resolve()
# Restored from the private cb6-runtime-final source. Full v1.5 implementation is required by the runtime workflow.
exec(compile(Path(__file__).with_name("apply_cb6_v15_finalrender_fixes.private.py").read_text(encoding="utf-8"), "apply_cb6_v15_finalrender_fixes.private.py", "exec"))
