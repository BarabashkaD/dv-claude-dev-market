#!/usr/bin/env python
"""Validate plugin manifests and skills of a marketplace repo.

Usage: check_plugins.py [ROOT]

Checks: plugins listed in the Claude and Codex catalogs exist; versions agree
between plugin.json (Codex), .claude-plugin/plugin.json and the Claude catalog
(the Codex catalog has no version); every skills/*/SKILL.md has frontmatter with
name == folder name and description <= 1024 chars; SKILL.md over 150 lines warns.
Exit 1 on errors; warnings do not affect the exit code.
"""
import glob
import json
import os
import sys

MAX_DESC = 1024
MAX_LINES = 150


def load(path, errors):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        errors.append("%s: cannot read JSON (%s)" % (path, exc))
        return None


def frontmatter(text):
    """Parse flat `key: value` frontmatter (supports > and | block scalars)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    out, key = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        if line[:1] in (" ", "\t") and key:
            out[key] = (out[key] + " " + line.strip()).strip()
        elif ":" in line:
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if val in (">", "|", ">-", "|-"):
                val = ""
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            out[key] = val
    return None  # no closing delimiter


def check_skill(path, errors, warnings):
    folder = os.path.basename(os.path.dirname(path))
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    fm = frontmatter(text)
    if fm is None:
        errors.append("%s: missing or unterminated frontmatter" % path)
        return
    if fm.get("name") != folder:
        errors.append("%s: name %r does not match folder %r" % (path, fm.get("name"), folder))
    desc = fm.get("description", "")
    if not desc:
        errors.append("%s: missing description" % path)
    elif len(desc) > MAX_DESC:
        errors.append("%s: description is %d chars (max %d)" % (path, len(desc), MAX_DESC))
    n = len(text.splitlines())
    if n > MAX_LINES:
        warnings.append("%s: warning: %d lines (over %d)" % (path, n, MAX_LINES))


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    root = args[0] if args else "."
    errors, warnings = [], []

    claude_cat = os.path.join(root, ".claude-plugin", "marketplace.json")
    codex_cat = os.path.join(root, ".agents", "plugins", "marketplace.json")
    claude_versions, dirs, codex_names = {}, {}, set()

    if os.path.exists(claude_cat):
        data = load(claude_cat, errors) or {}
        for p in data.get("plugins", []):
            dirs[p["name"]] = os.path.normpath(os.path.join(root, p.get("source", "")))
            claude_versions[p["name"]] = p.get("version")
    if os.path.exists(codex_cat):
        data = load(codex_cat, errors) or {}
        for p in data.get("plugins", []):
            src = p.get("source", {})
            path = src.get("path", "") if isinstance(src, dict) else src
            codex_names.add(p["name"])
            dirs.setdefault(p["name"], os.path.normpath(os.path.join(root, path)))

    for name, d in sorted(dirs.items()):
        if not os.path.isdir(d):
            errors.append("%s: plugin directory missing (%s)" % (name, d))
            continue
        codex = os.path.join(d, "plugin.json")
        claude = os.path.join(d, ".claude-plugin", "plugin.json")
        versions = {}
        if name in codex_names and not os.path.exists(codex):
            errors.append("%s: Codex catalog entry but no root plugin.json (%s)" % (name, codex))
        for label, p in (("plugin.json", codex), (".claude-plugin/plugin.json", claude)):
            if os.path.exists(p):
                mf = load(p, errors) or {}
                versions[label] = mf.get("version")
                if mf.get("name") != name:
                    errors.append("%s: %s name %r differs from catalog name"
                                  % (name, label, mf.get("name")))
        if name in claude_versions:
            versions["claude catalog"] = claude_versions[name]
        if len(set(versions.values())) > 1:
            errors.append("%s: version mismatch %s" % (name, versions))

    skill_files = glob.glob(os.path.join(root, "plugins", "*", "skills", "*", "SKILL.md"))
    for path in sorted(skill_files):
        check_skill(path, errors, warnings)

    for line in warnings + errors:
        print(line)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
