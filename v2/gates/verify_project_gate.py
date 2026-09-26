#!/usr/bin/env python3
import json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
STATE=ROOT/"v2/gates/project_state.json"
EXEC=ROOT/"docs/CB6_DEVELOPMENT_EXECUTION_GATE.md"
OLD=ROOT/"docs/CB6_V2_OVERALL_SYSTEM_DESIGN.md"
def fail(msg):
 print("CB6 DEVELOPMENT GATE FAIL:",msg); raise SystemExit(1)
for p in (STATE,EXEC,OLD):
 if not p.exists(): fail("required gate input missing: "+str(p.relative_to(ROOT)))
s=json.loads(STATE.read_text(encoding="utf-8"))
if s.get("schema")!=1: fail("unsupported project_state schema")
if s.get("branch")!="cb6-v2-clean": fail("wrong branch authority")
stage=s.get("stage")
if stage not in {"OVERALL_DESIGN_REBUILD","IMPLEMENTATION_ENABLED"}: fail("unknown stage: "+str(stage))
old=OLD.read_text(encoding="utf-8")
if "RETIRED AS CANONICAL" not in old: fail("retired overall design became canonical again")
if stage=="OVERALL_DESIGN_REBUILD":
 if s.get("feature_builds_allowed") is not False: fail("feature builds must be disabled during design rebuild")
 print("CB6 DEVELOPMENT GATE PASS: overall-design rebuild; feature builds BLOCKED")
 if "--require-feature-build" in sys.argv: fail("feature build requested while overall design rebuild is active")
 raise SystemExit(0)
canonical=ROOT/s.get("canonical_design","")
if not canonical.is_file(): fail("canonical rebuilt design missing")
if not s.get("design_verified"): fail("rebuilt design not verified")
if s.get("feature_builds_allowed") is not True: fail("feature builds not authorized")
print("CB6 DEVELOPMENT GATE PASS: implementation enabled")
