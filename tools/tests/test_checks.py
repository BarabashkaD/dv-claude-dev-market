"""Tests for tools/check_public.py and tools/check_plugins.py (stdlib + pytest)."""
import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent

# Sensitive fragments are assembled so this file does not trip the checker.
USERS_PATH = "/Us" + "ers/x/a.md"
TILDE_PATH = "~/" + ".claude/x"
HOME_VAR = "$HO" + "ME/foo"
WIN_PATH = "C:" + "\\Us" + "ers\\x"


def run(script, *args, stdin=None):
    return subprocess.run(
        [sys.executable, "-I", str(TOOLS / script), *map(str, args)],
        input=stdin, capture_output=True, text=True,
    )


def public(tmp_path, text, *extra, name="a.md"):
    (tmp_path / name).write_text(text, encoding="utf-8")
    return run("check_public.py", *extra, tmp_path)


# ---- check_public ----------------------------------------------------------

def test_user_path_fails(tmp_path):
    r = public(tmp_path, "see " + USERS_PATH + "\n")
    assert r.returncode == 1
    assert "a.md:1:" in r.stdout


def test_tilde_path_fails(tmp_path):
    assert public(tmp_path, TILDE_PATH + "\n").returncode == 1


def test_home_var_and_windows_path_fail(tmp_path):
    assert public(tmp_path, HOME_VAR + "\n").returncode == 1
    assert public(tmp_path, WIN_PATH + "\n", name="b.md").returncode == 1


def test_denylist_word_fails_case_insensitive(tmp_path):
    deny = tmp_path / "deny.txt"
    deny.write_text("# projects\nSecretProj\n", encoding="utf-8")
    sub = tmp_path / "repo"
    sub.mkdir()
    (sub / "a.md").write_text("ok\nmentions secretPROJ here\n", encoding="utf-8")
    r = run("check_public.py", "--denylist", deny, sub)
    assert r.returncode == 1
    assert "a.md:2:" in r.stdout
    assert "SecretProj" not in r.stdout  # the word itself is not echoed


def test_denylist_ignores_comments_and_blank_lines(tmp_path):
    deny = tmp_path / "deny.txt"
    deny.write_text("# secretproj category\n\n", encoding="utf-8")
    sub = tmp_path / "repo"
    sub.mkdir()
    (sub / "a.md").write_text("secretproj\n", encoding="utf-8")
    assert run("check_public.py", "--denylist", deny, sub).returncode == 0


def test_noreply_addresses_pass(tmp_path):
    assert public(tmp_path, "1+Someone@users.noreply.github.com\n").returncode == 0
    assert public(tmp_path, "Co-Authored-By: X <noreply@anthropic.com>\n",
                  name="b.md").returncode == 0


def test_other_email_fails(tmp_path):
    assert public(tmp_path, "mail me: someone" + "@example.com\n").returncode == 1
    assert public(tmp_path, "x" + "@anthropic.com\n", name="b.md").returncode == 1


def test_clean_text_passes(tmp_path):
    r = public(tmp_path, "# Title\n\nPlain text, @types/node, 3 * 4.\n")
    assert r.returncode == 0
    assert r.stdout == ""


def test_stdin_mode(tmp_path):
    bad = run("check_public.py", "--stdin", stdin="x\n" + USERS_PATH + "\n")
    assert bad.returncode == 1
    assert "<stdin>:2:" in bad.stdout
    ok = run("check_public.py", "--stdin", stdin="all fine\n")
    assert ok.returncode == 0


def test_allowlist_masks_substring(tmp_path):
    allow = tmp_path / "allow.txt"
    allow.write_text("# ok\nlegit-name\n", encoding="utf-8")
    deny = tmp_path / "deny.txt"
    deny.write_text("legit-name\n", encoding="utf-8")
    sub = tmp_path / "repo"
    sub.mkdir()
    (sub / "a.md").write_text("see legit-name\n", encoding="utf-8")
    assert run("check_public.py", "--denylist", deny, sub).returncode == 1
    r = run("check_public.py", "--denylist", deny, "--allowlist", allow, sub)
    assert r.returncode == 0


def test_home_var_prefix_of_longer_name_passes(tmp_path):
    assert public(tmp_path, "\"$HO" + "ME_DIR\"\n").returncode == 0


def test_allowlist_file_masks_itself(tmp_path):
    allow = tmp_path / "allow.txt"
    allow.write_text("# c\n" + TILDE_PATH + "\n", encoding="utf-8")
    sub = tmp_path / "repo"
    sub.mkdir()
    (sub / "a.md").write_text("x " + TILDE_PATH + " y\n", encoding="utf-8")
    (sub / "allow.txt").write_text(allow.read_text(encoding="utf-8"), encoding="utf-8")
    assert run("check_public.py", "--allowlist", allow, sub).returncode == 0
    assert run("check_public.py", sub).returncode == 1


def test_git_dir_skipped(tmp_path):
    g = tmp_path / ".git"
    g.mkdir()
    (g / "config").write_text(USERS_PATH + "\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("fine\n", encoding="utf-8")
    assert run("check_public.py", tmp_path).returncode == 0


# ---- check_plugins ---------------------------------------------------------

def make_repo(tmp_path, codex_ver="1.0.0", claude_ver="1.0.0", market_ver="1.0.0",
              skill_name="demo-skill", skill_dir="demo-skill", desc="Does a thing.",
              body_lines=3):
    root = tmp_path / "r"
    plug = root / "plugins" / "demo"
    (plug / ".claude-plugin").mkdir(parents=True)
    (plug / "plugin.json").write_text(
        json.dumps({"name": "demo", "version": codex_ver}), encoding="utf-8")
    (plug / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "demo", "version": claude_ver}), encoding="utf-8")
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
        "name": "m", "plugins": [{"name": "demo", "version": market_ver,
                                  "source": "./plugins/demo"}]}), encoding="utf-8")
    (root / ".agents" / "plugins").mkdir(parents=True)
    (root / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps({
        "name": "m", "plugins": [{"name": "demo", "source": {
            "source": "local", "path": "./plugins/demo"}}]}), encoding="utf-8")
    sk = plug / "skills" / skill_dir
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: {desc}\n---\n\n"
        + "line\n" * body_lines, encoding="utf-8")
    return root


def test_plugins_ok(tmp_path):
    r = run("check_plugins.py", make_repo(tmp_path))
    assert r.returncode == 0, r.stdout


def test_manifest_version_mismatch_fails(tmp_path):
    r = run("check_plugins.py", make_repo(tmp_path, codex_ver="1.1.0"))
    assert r.returncode == 1
    assert "version" in r.stdout


def test_catalog_version_mismatch_fails(tmp_path):
    assert run("check_plugins.py", make_repo(tmp_path, market_ver="2.0.0")).returncode == 1


def test_skill_name_mismatch_fails(tmp_path):
    r = run("check_plugins.py", make_repo(tmp_path, skill_name="other"))
    assert r.returncode == 1
    assert "name" in r.stdout


def test_description_too_long_fails(tmp_path):
    assert run("check_plugins.py", make_repo(tmp_path, desc="x" * 1025)).returncode == 1


def test_long_skill_warns_only(tmp_path):
    r = run("check_plugins.py", make_repo(tmp_path, body_lines=200))
    assert r.returncode == 0
    assert "warning" in r.stdout.lower()


def test_missing_plugin_dir_fails(tmp_path):
    root = make_repo(tmp_path)
    import shutil
    shutil.rmtree(root / "plugins" / "demo")
    assert run("check_plugins.py", root).returncode == 1


def test_allowlist_in_repo_does_not_mask_new_paths_under_same_dir(tmp_path):
    allow = TOOLS / "public-allowlist.txt"
    sub = tmp_path / "repo"
    sub.mkdir()
    (sub / "a.md").write_text("see ~/" + ".claude/venvs/secret-project/x\n"
                              "or ~/" + ".claude/skills/private-skill/y\n", encoding="utf-8")
    r = run("check_public.py", "--allowlist", allow, sub)
    assert r.returncode == 1
    assert "a.md:1:" in r.stdout and "a.md:2:" in r.stdout


def test_tilde_other_dirs_fail(tmp_path):
    for d in ("Desk" + "top", "Lib" + "rary", "Proj" + "ects"):
        assert public(tmp_path, "cd ~/" + d + "/x\n").returncode == 1, d


def test_tilde_alone_or_non_letter_passes(tmp_path):
    assert public(tmp_path, "use ~/ or ~/" + "1 or ~/ x\n").returncode == 0


def test_binary_content_not_scanned_for_tilde(tmp_path):
    (tmp_path / "b.png").write_bytes(b"\x00\x01 ~/" + b"ab \x00")
    assert run("check_public.py", tmp_path).returncode == 0


def test_path_name_scanned(tmp_path):
    (tmp_path / "secret-proj-x.md").write_text("fine\n", encoding="utf-8")
    deny = tmp_path.parent / (tmp_path.name + "-deny.txt")
    deny.write_text("secret-proj\n", encoding="utf-8")
    r = run("check_public.py", "--denylist", deny, tmp_path)
    assert r.returncode == 1
    assert "secret-proj-x.md: " in r.stdout and "denylist" in r.stdout


def test_path_name_with_user_path_fails(tmp_path):
    d = tmp_path / ("a" + "$HO" + "ME.d")
    d.mkdir()
    (d / "ok.md").write_text("fine\n", encoding="utf-8")
    r = run("check_public.py", tmp_path)
    assert r.returncode == 1


def test_codex_plugin_without_root_manifest_fails(tmp_path):
    root = make_repo(tmp_path)
    (root / "plugins" / "demo" / "plugin.json").unlink()
    r = run("check_plugins.py", root)
    assert r.returncode == 1
    assert "plugin.json" in r.stdout


def test_manifest_name_differs_from_catalog_fails(tmp_path):
    root = make_repo(tmp_path)
    p = root / "plugins" / "demo" / "plugin.json"
    p.write_text(json.dumps({"name": "other", "version": "1.0.0"}), encoding="utf-8")
    r = run("check_plugins.py", root)
    assert r.returncode == 1
    assert "name" in r.stdout
