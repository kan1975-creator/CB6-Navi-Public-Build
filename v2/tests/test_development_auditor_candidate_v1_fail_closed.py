#!/usr/bin/env python3
import json, shutil, subprocess, tempfile
from pathlib import Path

S = Path(__file__).resolve().parents[2]
CMD = ["python3", "v2/gates/verify_development_auditor_candidate_v1.py"]

def run(r):
    return subprocess.run(CMD, cwd=r, text=True, capture_output=True)

base = run(S)
if base.returncode:
    raise SystemExit("auditor candidate baseline failed\n" + base.stdout + base.stderr)

cases = [
    ("stale-head-allowed", lambda d: d["freshness"].update({"head_change_requires_resynchronization": False}), "freshness guard missing"),
    ("chat-memory-authority", lambda d: d["freshness"].update({"chat_memory_is_not_authority": False}), "freshness guard missing"),
    ("drop-research", lambda d: d["audit_dimensions"].remove("multidirectional_research"), "audit dimensions missing"),
    ("reuse-future-approval", lambda d: d["approval_boundary"].update({"unknown_future_change_may_reuse_prior_approval": True}), "approval reuse not forbidden"),
    ("allow-app-change", lambda d: d["non_interference"].update({"application_source_change_forbidden": False}), "non-interference guard missing"),
    ("self-activate", lambda d: d.update({"status": "ACTIVE"}), "candidate identity/status invalid"),
    ("drop-independent-review", lambda d: d["activation"]["requires_before_active"].remove("independent_review"), "activation prerequisite missing"),
]
for name, mut, needle in cases:
    with tempfile.TemporaryDirectory() as td:
        r = Path(td) / "repo"
        shutil.copytree(S, r, ignore=shutil.ignore_patterns(".git", "out", "comaps"))
        p = r / "v2/gates/development_auditor_candidate_v1.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        mut(d)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        cp = run(r)
        out = cp.stdout + cp.stderr
        if cp.returncode == 0 or needle not in out:
            raise SystemExit(name + " not rejected\n" + out)
        print("PASS expected auditor rejection:", name)

with tempfile.TemporaryDirectory() as td:
    r = Path(td) / "repo"
    shutil.copytree(S, r, ignore=shutil.ignore_patterns(".git", "out", "comaps"))
    p = r / "v2/gates/rule_coverage.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["entries"].append({"rule_id": "CB6-DEVELOPMENT-AUDITOR-V1", "coverage_status": "MACHINE_ENFORCED"})
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cp = run(r)
    out = cp.stdout + cp.stderr
    if cp.returncode == 0 or "candidate illegally entered ACTIVE rule coverage" not in out:
        raise SystemExit("premature coverage not rejected\n" + out)
    print("PASS expected auditor rejection: premature ACTIVE coverage")

print("PASS development auditor candidate destructive cases rejected")
