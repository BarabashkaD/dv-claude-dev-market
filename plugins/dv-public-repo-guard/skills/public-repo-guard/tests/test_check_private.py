"""Tests for scripts/check_private.py, scripts/strip_png_text.py and assets/pre-commit (stdlib + pytest).

Every check is shown failing on an injected fault and passing on the same input without it. Fixtures
are generated here at runtime; sensitive fragments are assembled so this file does not trip
tools/check_public.py or the guard itself.
"""
import io
import os
import shutil
import struct
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
GUARD = SKILL / "scripts" / "check_private.py"
STRIP = SKILL / "scripts" / "strip_png_text.py"
HOOK = SKILL / "assets" / "pre-commit"
REPO = SKILL.parents[3]

MAC_HOME = "/" + "Users" + "/someone/project/render.png"
LINUX_HOME = "/" + "home" + "/someone/project/part.step"
WIN_HOME = "C:" + "\\" + "Users" + "\\someone\\project\\photo.jpg"
WIN_HOME_JSON = "C:" + "\\\\" + "Users" + "\\\\someone\\\\x"
EMAIL = "someone" + "@" + "example.org"
GITHUB_NOREPLY = "12345+someone" + "@" + "users.noreply.github.com"
ANTHROPIC_NOREPLY = "noreply" + "@" + "anthropic.com"
CLEAN_TEXT = "see docs/part.step and <archive>/renders/front.png\n"


# ---- fixture builders -------------------------------------------------------

def chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def png(*extra):
    """A valid 1x1 grey PNG with the given extra chunks before IDAT."""
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\x80"))
    return b"\x89PNG\r\n\x1a\n" + ihdr + b"".join(extra) + idat + chunk(b"IEND", b"")


def text_chunk(key, text):
    return chunk(b"tEXt", key + b"\0" + text.encode("latin-1"))


def ztxt_chunk(key, text):
    return chunk(b"zTXt", key + b"\0\0" + zlib.compress(text.encode("latin-1")))


def itxt_chunk(key, text, compressed=True):
    data = zlib.compress(text.encode("utf-8")) if compressed else text.encode("utf-8")
    return chunk(b"iTXt", key + b"\0" + bytes([int(compressed), 0]) + b"en\0\0" + data)


def jpeg(comment=None, sos=True):
    seg = b""
    if comment is not None:
        body = comment.encode("utf-8")
        seg = b"\xff\xfe" + struct.pack(">H", len(body) + 2) + body
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\0\x01\x01\0\0\x01\0\x01\0\0"
    tail = b"\xff\xda" + struct.pack(">H", 2) + b"\x12\x34" + b"\xff\xd9" if sos else b""
    return b"\xff\xd8" + app0 + seg + tail


def zip_bytes(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buf.getvalue()


def fcstd(path_prop):
    doc = '<Document><Property name="Notes"><String value="%s"/></Property></Document>' % path_prop
    return zip_bytes({"Document.xml": doc, "GuiDocument.xml": "<Document/>",
                      "PartShape.brp": b"\0binary\0"})


def run(script, *args, cwd=None, env=None):
    return subprocess.run([sys.executable, "-I", str(script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd, env=env)


def guard(tmp_path, name, data):
    p = tmp_path / name
    p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return run(GUARD, p)


# ---- each check: clean input passes, injected fault fails --------------------

CASES = [
    # id, file name, clean content, faulty content, expected text in the finding
    ("plain text home path", "notes.md", CLEAN_TEXT, "output in %s\n" % MAC_HOME, "home path"),
    ("plain text linux home", "run.log", CLEAN_TEXT, "wrote %s\n" % LINUX_HOME, "home path"),
    ("plain text windows path", "cfg.json", '{"p": "x"}\n', '{"p": "%s"}\n' % WIN_HOME_JSON,
     "windows home path"),
    ("png tEXt e-mail", "a.png", png(text_chunk(b"Software", "FreeCAD")),
     png(text_chunk(b"Author", EMAIL)), "a.png:Author:1: e-mail"),
    ("png compressed iTXt home path", "b.png", png(itxt_chunk(b"Comment", "front view")),
     png(itxt_chunk(b"Comment", "saved from " + MAC_HOME)), "b.png:Comment:1: home path"),
    ("png zTXt Title home path (FreeCAD saveImage)", "c.png", png(ztxt_chunk(b"Title", "render.png")),
     png(ztxt_chunk(b"Title", MAC_HOME)), "c.png:Title:1: home path"),
    ("png eXIf home path", "d.png", png(chunk(b"eXIf", b"MM\0*clean")),
     png(chunk(b"eXIf", b"MM\0*" + LINUX_HOME.encode())), "d.png:eXIf:1: home path"),
    ("png corrupt zTXt", "e.png", png(ztxt_chunk(b"Title", "ok")),
     png(chunk(b"zTXt", b"Title\0\0not zlib data")), "unreadable image metadata"),
    ("non-image .png", "f.png", png(), b"just text pretending to be an image\n", "not a PNG or JPEG"),
    ("jpeg COM windows path", "g.jpg", jpeg("made with a camera"), jpeg("file " + WIN_HOME),
     "g.jpg:FE:1: windows home path"),
    ("jpeg without start of scan", "h.jpeg", jpeg(), jpeg(sos=False), "unreadable image metadata"),
    ("FCStd Document.xml home path", "model.FCStd", fcstd("from parts/a.step"), fcstd(MAC_HOME),
     "model.FCStd:Document.xml:1: home path"),
    ("3mf e-mail in metadata", "plate.3mf",
     zip_bytes({"3D/3dmodel.model": "x", "Metadata/model_settings.config": "<config/>"}),
     zip_bytes({"Metadata/model_settings.config": "<author>%s</author>" % EMAIL}), "e-mail"),
    ("docx core properties e-mail", "report.docx",
     zip_bytes({"docProps/core.xml": "<creator>A. Person</creator>"}),
     zip_bytes({"docProps/core.xml": "<creator>%s</creator>" % EMAIL}),
     "report.docx:docProps/core.xml:1: e-mail"),
    ("PNG member inside a zip", "bundle.zip", zip_bytes({"thumbnails/t.png": png()}),
     zip_bytes({"thumbnails/t.png": png(ztxt_chunk(b"Title", MAC_HOME))}),
     "bundle.zip:thumbnails/t.png:Title:1: home path"),
    ("corrupt zip", "broken.FCStd", fcstd("ok"), b"PK\x03\x04 truncated", "not a readable zip"),
    ("other e-mail", "AUTHORS", "Some One <%s>\n" % GITHUB_NOREPLY, "Some One <%s>\n" % EMAIL, "e-mail"),
]


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_clean_passes(tmp_path, case):
    _, name, clean, _, _ = case
    r = guard(tmp_path, name, clean)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout == ""


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_injected_fault_fails(tmp_path, case):
    _, name, _, dirty, expected = case
    r = guard(tmp_path, name, dirty)
    assert r.returncode == 1, r.stdout + r.stderr
    assert expected in r.stdout, r.stdout
    assert "finding(s)" in r.stderr


def test_allowed_noreply_addresses_pass(tmp_path):
    text = "Co-Authored-By: Claude <%s>\nAuthor: <%s>\n" % (ANTHROPIC_NOREPLY, GITHUB_NOREPLY)
    r = guard(tmp_path, "COMMIT_NOTES.md", text)
    assert r.returncode == 0, r.stdout


def test_skipped_extensions_are_not_scanned(tmp_path):
    for name in ("part.step", "part.brep", "mesh.stl", "doc.pdf"):
        r = guard(tmp_path, name, "FILE_NAME('%s')\n" % MAC_HOME)
        assert r.returncode == 0, name


def test_other_binary_files_are_skipped(tmp_path):
    r = guard(tmp_path, "blob.bin", b"\0\0" + MAC_HOME.encode())
    assert r.returncode == 0


def test_hint_default_cli_and_env(tmp_path):
    p = tmp_path / "a.md"
    p.write_text(MAC_HOME + "\n", encoding="utf-8")
    assert "relative to the repository root" in run(GUARD, p).stderr
    assert "use <archive>/" in run(GUARD, "--hint", "use <archive>/", p).stderr
    env = dict(os.environ, CHECK_PRIVATE_HINT="env hint here")
    assert "env hint here" in run(GUARD, p, env=env).stderr


# ---- --staged mode and the hook template, in a temporary git repository ----

def git_env():
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME="t", GIT_COMMITTER_NAME="t",
               GIT_AUTHOR_EMAIL=GITHUB_NOREPLY, GIT_COMMITTER_EMAIL=GITHUB_NOREPLY,
               CHECK_PRIVATE_PYTHON=sys.executable)
    env.pop("CHECK_PRIVATE_HINT", None)
    return env


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=git_env())


@pytest.fixture
def repo(tmp_path):
    if not shutil.which("git"):
        pytest.skip("git not installed")
    r = tmp_path / "repo"
    r.mkdir()
    assert git(r, "init", "-q").returncode == 0
    return r


def staged(repo):
    return subprocess.run([sys.executable, "-I", str(GUARD), "--staged"], cwd=repo,
                          capture_output=True, text=True, env=git_env())


def test_staged_mode(repo):
    (repo / "ok.md").write_text(CLEAN_TEXT, encoding="utf-8")
    (repo / "c.png").write_bytes(png(ztxt_chunk(b"Title", MAC_HOME)))
    (repo / "untracked.md").write_text(MAC_HOME, encoding="utf-8")   # not staged: not scanned
    git(repo, "add", "ok.md")
    r = staged(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    git(repo, "add", "c.png")
    r = staged(repo)
    assert r.returncode == 1 and "c.png:Title:1: home path" in r.stdout, r.stdout
    assert "untracked.md" not in r.stdout


def test_staged_mode_scans_the_index_not_the_working_tree(repo):
    p = repo / "notes.md"
    p.write_text(MAC_HOME + "\n", encoding="utf-8")
    git(repo, "add", "notes.md")
    p.write_text(CLEAN_TEXT, encoding="utf-8")       # cleaned on disk but not re-staged
    r = staged(repo)
    assert r.returncode == 1 and "notes.md:1: home path" in r.stdout, r.stdout
    git(repo, "add", "notes.md")
    assert staged(repo).returncode == 0


def test_staged_mode_rename_and_subdir(repo):
    (repo / "sub").mkdir()
    (repo / "sub" / "a.md").write_text(CLEAN_TEXT, encoding="utf-8")
    git(repo, "add", ".")
    assert git(repo, "commit", "-q", "-m", "init").returncode == 0
    git(repo, "mv", "sub/a.md", "sub/b.md")
    (repo / "sub" / "b.md").write_text(CLEAN_TEXT + "x " + EMAIL + "\n", encoding="utf-8")
    git(repo, "add", ".")
    r = subprocess.run([sys.executable, "-I", str(GUARD), "--staged"], cwd=repo / "sub",
                       capture_output=True, text=True, env=git_env())
    assert r.returncode == 1 and "sub/b.md:2: e-mail" in r.stdout, r.stdout + r.stderr


def test_staged_outside_git_is_exit_2(tmp_path):
    env = dict(git_env(), GIT_CEILING_DIRECTORIES=str(tmp_path))
    r = subprocess.run([sys.executable, "-I", str(GUARD), "--staged"], cwd=tmp_path,
                       capture_output=True, text=True, env=env)
    assert r.returncode == 2, r.stdout + r.stderr


def install_hook(repo):
    (repo / "tools").mkdir()
    (repo / ".githooks").mkdir()
    shutil.copy(GUARD, repo / "tools" / "check_private.py")
    shutil.copy(HOOK, repo / ".githooks" / "pre-commit")
    os.chmod(repo / ".githooks" / "pre-commit", 0o755)
    git(repo, "config", "core.hooksPath", ".githooks")


def test_hook_template_blocks_and_allows(repo):
    install_hook(repo)
    (repo / "model.FCStd").write_bytes(fcstd(MAC_HOME))
    git(repo, "add", ".")
    r = git(repo, "commit", "-q", "-m", "dirty")
    assert r.returncode != 0 and "model.FCStd:Document.xml:1: home path" in r.stdout + r.stderr
    (repo / "model.FCStd").write_bytes(fcstd("parts/a.step"))
    git(repo, "add", ".")
    r = git(repo, "commit", "-q", "-m", "clean")
    assert r.returncode == 0, r.stdout + r.stderr


def test_hook_template_fails_closed(repo):
    install_hook(repo)
    (repo / "ok.md").write_text(CLEAN_TEXT, encoding="utf-8")
    git(repo, "add", "ok.md")
    env = dict(git_env(), CHECK_PRIVATE_PYTHON="no-such-python-interpreter")
    r = subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=repo, capture_output=True,
                       text=True, env=env)
    assert r.returncode != 0
    os.remove(repo / "tools" / "check_private.py")
    r = git(repo, "commit", "-q", "-m", "x")
    assert r.returncode != 0 and "not found" in r.stderr


# ---- strip_png_text.py --------------------------------------------------------

def idat(data):
    i, out = 8, []
    while i < len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        if kind not in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
            out.append(data[i:i + 12 + n])
        i += 12 + n
    return out


def test_strip_removes_text_chunks_and_keeps_pixels(tmp_path):
    p = tmp_path / "render.png"
    before = png(ztxt_chunk(b"Title", MAC_HOME), text_chunk(b"Author", EMAIL), itxt_chunk(b"C", "x"))
    p.write_bytes(before)
    assert run(GUARD, p).returncode == 1
    r = run(STRIP, p)
    assert r.returncode == 0 and "removed 3 chunk(s)" in r.stdout, r.stdout
    after = p.read_bytes()
    assert idat(after) == idat(before)                      # every non-text chunk byte for byte
    assert run(GUARD, p).returncode == 0


def test_strip_refuses_non_png(tmp_path):
    p = tmp_path / "fake.png"
    p.write_bytes(b"not a png")
    r = run(STRIP, p)
    assert r.returncode == 1 and "not changed" in r.stdout
    assert p.read_bytes() == b"not a png"


# ---- the skill's own files are publishable ------------------------------------

def test_skill_files_pass_both_guards(tmp_path):
    files = [p for p in SKILL.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    r = run(GUARD, *files)
    assert r.returncode == 0, r.stdout
    res = subprocess.run(
        [sys.executable, "-I", str(REPO / "tools" / "check_public.py"),
         "--allowlist", str(REPO / "tools" / "public-allowlist.txt"), str(SKILL)],
        capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
