---
name: python-venv-manager
description: Global Python environment manager for ALL Claude skills. Use this any time a skill (document-skills:pdf/docx/xlsx/pptx, huggingface-skills:*, or any other skill) needs to run Python code, execute a Python-based script/tool, or install pip packages. ALWAYS consult this before running `python3`, `pip install`, or similar commands on behalf of another skill's instructions — never install packages into the system Python. Creates and reuses one virtual environment per skill under a per-user Claude venvs directory so environments persist across sessions and projects instead of being rebuilt every time.
---

# Python Venv Manager

## Why this exists

Many skills (PDF/DOCX/XLSX processing, Hugging Face tooling, etc.) tell you to
`pip install` something and run a Python script. Done naively, that either
pollutes the system Python or forces you to rebuild the same environment
every single session and every project. This skill makes environments
per-skill and persistent: create once, reuse forever, never collide with
another skill's dependencies.

## Locating the bundled script

This skill ships `scripts/ensure_venv.sh` next to this file — do not
hardcode an absolute path to it. When this skill is invoked, Claude Code
reports where it actually lives, e.g.:

```
Base directory for this skill: /path/to/.../skills/python-venv-manager
```

Build the script path from that announced directory:

```bash
SCRIPT="<base-directory-from-above>/scripts/ensure_venv.sh"
```

The base directory differs depending on how this skill got installed
(plugin cache, a project-local `.claude/skills/`, etc.) — always resolve it
from the invocation, never assume `~/.claude/skills/...` or any other fixed
location.

## Workflow

1. **Identify the skill name** that needs Python (its `name:` field or
   plugin-qualified id, e.g. `document-skills:pdf`).

2. **Ask for its venv** using the bundled script — with no install
   arguments first:

   ```bash
   PYTHON_BIN=$(bash "$SCRIPT" "document-skills:pdf")
   ```

   If a venv already exists for that skill, the script prints its python
   path and does nothing else. **Trust it. Do not re-check installed
   packages, do not re-run pip, do not inspect anything further** — that
   defeats the entire point of reusing environments across sessions.

3. **Only if the venv doesn't exist yet** (first time this skill has ever
   needed Python on this machine), the script needs to know what to
   install. Work out the packages in this order, cheapest/most authoritative
   first:

   a. Look for a manifest already shipped with the target skill —
      `requirements.txt`, a `pyproject.toml` dependency list, or an
      explicit `pip install ...` line in its SKILL.md/reference docs. If
      found, pass its path:

      ```bash
      PYTHON_BIN=$(bash "$SCRIPT" "document-skills:pdf" /path/to/requirements.txt)
      ```

   b. If no manifest exists, read the skill's SKILL.md/scripts yourself to
      infer what it needs (import statements, documented `pip install`
      commands) and pass them as package names instead:

      ```bash
      PYTHON_BIN=$(bash "$SCRIPT" "document-skills:pdf" pypdf pdfplumber reportlab)
      ```

4. **Run everything through that interpreter directly** — no
   `source activate` / `deactivate` needed. Each Bash call may be a fresh
   shell anyway, so activation wouldn't reliably persist between calls;
   calling the binary by full path gives the same isolation with no
   fragility:

   ```bash
   "$PYTHON_BIN" script.py
   "$PYTHON_BIN" -c "import pypdf; print(pypdf.__version__)"
   ```

   For an extra package mid-task, use pip from that same venv (it sits
   next to the python binary on every platform — `Scripts/` on Windows,
   `bin/` everywhere else):

   ```bash
   "$(dirname "$PYTHON_BIN")/pip" install some-extra-package
   ```

## Platform behavior

The script auto-detects everything platform-specific instead of assuming
a Unix layout, so it runs unmodified on Linux, macOS, WSL, and Git Bash on
Windows:

- **Home directory**: uses `$HOME`, falling back to `$USERPROFILE` if unset.
- **Venv layout**: checks for `bin/python` (POSIX) or `Scripts/python.exe`
  (Windows) rather than hardcoding one.
- **Python launcher**: tries `python3`, then `python`, then the Windows
  `py -3` launcher, whichever is first found on `PATH`.

## Naming and location

- Venvs live under `$CLAUDE_VENV_ROOT` if set, otherwise
  `<home-directory>/.claude/venvs/<sanitized-skill-name>/`.
- Sanitization replaces `:`, `/`, and spaces with `-`
  (e.g. `document-skills:pdf` → `document-skills-pdf`).
- One venv per skill, kept indefinitely — never shared across skills, never
  auto-deleted.

## What not to do

- Don't create one shared venv for multiple skills — different skills can
  need conflicting package versions.
- Don't `pip install` into the system Python or any default/global venv.
- Don't re-verify or reinstall packages on every run once a skill's venv
  exists — existence alone means "trust it and move on."
- Don't bother with `source .../activate` and `deactivate` — call the
  venv's `python`/`pip` binaries by path instead.
- Don't hardcode this script's path in your own commands or messages —
  always resolve it from the skill's reported base directory.
