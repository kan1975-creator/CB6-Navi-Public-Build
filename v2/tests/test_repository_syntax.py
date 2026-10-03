#!/usr/bin/env python3
import ast, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
errors=[]
for p in sorted((ROOT/"v2").rglob("*.py")):
    try: ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except (SyntaxError,UnicodeDecodeError) as e: errors.append(f"{p.relative_to(ROOT)}: {e}")
for p in sorted((ROOT/"v2/gates").rglob("*.json")):
    try: json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError,UnicodeDecodeError) as e: errors.append(f"{p.relative_to(ROOT)}: {e}")
if errors:
    raise SystemExit("CB6 REPOSITORY SYNTAX FAIL:\n"+"\n".join(errors))
print("CB6 REPOSITORY SYNTAX PASS")
