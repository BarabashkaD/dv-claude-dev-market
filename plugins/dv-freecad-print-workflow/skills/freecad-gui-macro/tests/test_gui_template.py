"""Static checks of assets/gui_macro_template.py (stdlib + pytest only)."""
import ast
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "gui_macro_template.py"
REPO = SKILL.parents[3]


def _text():
    return TEMPLATE.read_text(encoding="utf-8")


def test_template_parses():
    ast.parse(_text())


def test_forbidden_substrings_absent():
    text = _text()
    for bad in ("Gui.activateDocument", ".grab().save(", "kill"):
        assert bad not in text, bad


def test_required_substrings_present():
    text = _text()
    for need in ("saveImage(", "getMainWindow().close()"):
        assert need in text, need


def test_template_defines_interface():
    names = {n.name for n in ast.parse(_text()).body if isinstance(n, ast.FunctionDef)}
    assert {"activate", "run", "finish"} <= names


def test_check_public_clean(tmp_path):
    shutil.copy(TEMPLATE, tmp_path / TEMPLATE.name)  # the checker scans directories
    res = subprocess.run(
        [sys.executable, "-I", str(REPO / "tools" / "check_public.py"),
         "--allowlist", str(REPO / "tools" / "public-allowlist.txt"), str(tmp_path)],
        capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr


def test_no_document_attribute_after_close():
    """`closeDocument(` must take a plain name, and `doc.Name` is not read after it."""
    lines = _text().splitlines()
    for i, line in enumerate(lines):
        if "closeDocument(" in line:
            assert ".Name" not in line, line
    run_src = _text().split("def run():")[1].split("def finish")[0]
    after_close = run_src.split("App.closeDocument(name)")[1].split("doc2 =")[0]
    assert "doc.Name" not in after_close and "doc.Label" not in after_close


def _pure_functions():
    """Load close_enough/same_facts/verify without FreeCAD (they work on plain dicts)."""
    tree = ast.parse(_text())
    wanted = {"close_enough", "same_facts", "verify"}
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    ns = {"PROBE_NAME": "GuiMacroProbe"}
    exec(compile(ast.Module(body=body, type_ignores=[]), "template", "exec"), ns)
    return ns


def _state(volume):
    return {"objects": 1, "visible": ["A"],
            "shapes": {"A": {"faces": 6, "solids": 1, "volume": volume}}}


def test_verify_tolerates_reload_noise():
    verify = _pure_functions()["verify"]
    assert verify(_state(1234.567891), _state(1234.567891 * (1 + 5e-8))) == []


def test_verify_detects_real_change():
    verify = _pure_functions()["verify"]
    assert verify(_state(1000.0), _state(1000.5))
    bad = _state(1000.0)
    bad["shapes"]["A"]["faces"] = 7
    assert verify(_state(1000.0), bad)
    assert verify(_state(1000.0), {"objects": 1, "visible": ["A"], "shapes": {}})
