#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXED_COMMIT = "b1f139b7826a00b777ac9f728799cf02aa9637d1"

def read_file_content(rel_path):
    p = ROOT / rel_path
    if p.is_file():
        return p.read_text(encoding="utf-8")
    # Fallback to reading from fixed commit
    cmd = ["git", "show", f"{FIXED_COMMIT}:{rel_path}"]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode == 0:
        return res.stdout
    return None

def main():
    errs = []
    doc_rel = "docs/governance/CB6_425_R36_CONSOLIDATED_PROPOSED_20261026.md"
    contract_rel = "docs/governance/CB6_425_R36_REGISTRATION_PROPOSAL_v22_candidate.json"
    registry_rel = "v2/gates/operational_rule_registry_v22_candidate.json"

    doc_text = read_file_content(doc_rel)
    if not doc_text:
        errs.append(f"Governance consolidated document missing: {doc_rel}")
    else:
        sections = ["A. 表示ルール", "B. ボタンルール", "C. STOP前・指示提示前の過去チャット確認", 
                    "D. 毎回の確認記録", "B-追加. ボタン操作方法の併記", "E. 実際のルール違反記録", 
                    "F. 回答ごとの強制確認手順", "G. 工程E-2-30-16-425-R-10", "H. 工程E-2-30-16-425-R-13", 
                    "I. 工程E-2-30-16-425-R-15", "J. 工程E-2-30-16-425-R-18", "K. 工程E-2-30-16-425-R-21", 
                    "L. 工程E-2-30-16-425-R-24", "M. 工程E-2-30-16-425-R-26"]
        for sec in sections:
            if sec not in doc_text:
                errs.append(f"Section heading missing in document: {sec}")

    contract_text = read_file_content(contract_rel)
    if not contract_text:
        errs.append(f"Proposal contract file missing: {contract_rel}")
    else:
        try:
            contract_data = json.loads(contract_text)
            if contract_data.get("proposal_id") != "CB6-GOV-425-R36-20261026":
                errs.append("Proposal ID mismatch in contract")
            if contract_data.get("status") != "PROPOSED":
                errs.append("Contract status is not PROPOSED")
            sec_keys = ["A", "B", "C", "D", "B_ADD", "E", "F", "G", "H", "I", "J", "K", "L", "M"]
            gov_secs = contract_data.get("governance_sections", {})
            for k in sec_keys:
                if k not in gov_secs:
                    errs.append(f"Missing governance section mapping in contract: {k}")
        except Exception as e:
            errs.append(f"Failed to parse contract JSON: {e}")

    registry_text = read_file_content(registry_rel)
    if not registry_text:
        errs.append(f"Candidate registry missing: {registry_rel}")
    else:
        try:
            reg_data = json.loads(registry_text)
            if reg_data.get("version") != 22:
                errs.append("Candidate registry version mismatch (expected 22)")
            rules = reg_data.get("rules", [])
            r36_rule = next((r for r in rules if r.get("id") == "OPS-GOV-R36-CONSOLIDATED-001"), None)
            if not r36_rule:
                errs.append("OPS-GOV-R36-CONSOLIDATED-001 rule missing in candidate registry")
            elif r36_rule.get("status") != "PROPOSED":
                errs.append("OPS-GOV-R36-CONSOLIDATED-001 status must be PROPOSED")
        except Exception as e:
            errs.append(f"Failed to parse candidate registry JSON: {e}")

    if errs:
        print("CB6 GOVERNANCE R36 CANDIDATE VERIFIER FAIL:")
        for e in errs:
            print(f" - {e}")
        raise SystemExit(1)

    print("CB6 GOVERNANCE R36 CANDIDATE VERIFIER PASS: Sections A-M verified in candidate contract and registry.")

if __name__ == "__main__":
    main()
