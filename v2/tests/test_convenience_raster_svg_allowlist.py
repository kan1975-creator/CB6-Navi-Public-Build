#!/usr/bin/env python3
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "v2/poi/apply_convenience_brand_render.py"
EXPECTED = {
    "cb6-seven.svg",
    "cb6-familymart.svg",
    "cb6-lawson.svg",
    "cb6-seicomart.svg",
    "cb6-ministop.svg",
    "cb6-mybasket.svg",
}

def load_policy():
    tree = ast.parse(SOURCE.read_text())
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CB6_RASTER_SVG_ALLOWLIST" for t in node.targets):
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "cb6_validate_svg_raster_policy":
            selected.append(node)
    ns = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), "exec"), ns)
    return ns["CB6_RASTER_SVG_ALLOWLIST"], ns["cb6_validate_svg_raster_policy"]

def test_allowlist_is_exactly_six_files():
    allowlist, _ = load_policy()
    assert set(allowlist) == EXPECTED
    assert len(allowlist) == 6

def test_each_exact_allowed_file_accepts_image_and_data_uri():
    _, validate = load_policy()
    raster = '<svg><image href="data:image/png;base64,AA=="/></svg>'
    for filename in EXPECTED:
        assert validate(filename, raster) is True

def test_non_allowlisted_svg_rejects_image_element():
    _, validate = load_policy()
    try:
        validate("cb6-daily.svg", '<svg><image href="x.png"/></svg>')
    except ValueError:
        pass
    else:
        raise AssertionError("non-allowlisted <image> was accepted")

def test_non_allowlisted_svg_rejects_data_image():
    _, validate = load_policy()
    try:
        validate("any-other.svg", '<svg><rect data-note="data:image/png;base64,AA=="/></svg>')
    except ValueError:
        pass
    else:
        raise AssertionError("non-allowlisted data:image was accepted")

def test_near_match_filename_is_rejected_fail_closed():
    _, validate = load_policy()
    raster = '<svg><image href="data:image/png;base64,AA=="/></svg>'
    for filename in ("CB6-seven.svg", "cb6-seven-copy.svg", "cb6-seven.svg.bak", "path/cb6-seven.svg"):
        try:
            validate(filename, raster)
        except ValueError:
            continue
        raise AssertionError("near-match filename was accepted: " + filename)

if __name__ == "__main__":
    tests = [
        test_allowlist_is_exactly_six_files,
        test_each_exact_allowed_file_accepts_image_and_data_uri,
        test_non_allowlisted_svg_rejects_image_element,
        test_non_allowlisted_svg_rejects_data_image,
        test_near_match_filename_is_rejected_fail_closed,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
