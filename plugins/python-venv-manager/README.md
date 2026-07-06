# python-venv-manager

Global Python environment manager for Claude Code skills.

Any skill that needs to run Python code or install pip packages should
route through this instead of touching the system Python directly. It
creates one virtual environment per skill under a per-user Claude venvs
directory (`~/.claude/venvs/` by default, `$CLAUDE_VENV_ROOT` to override)
and reuses it across sessions and projects, so environments aren't rebuilt
every time.

Runs on Linux, macOS, WSL, and Git Bash on Windows: home directory, venv
layout (`bin/` vs `Scripts/`), and python launcher (`python3`/`python`/`py`)
are all detected at runtime rather than assumed.

See `skills/python-venv-manager/SKILL.md` for the full workflow — in
particular, how to locate the bundled script relative to this skill's own
reported base directory instead of a hardcoded path.

## Enforcement hook

A `PreToolUse` hook on the `Bash` tool (`hooks/hooks.json` ->
`hooks/check-python-usage.sh`) blocks bare `python3`/`python`/`pip3`/`pip`
invocations and returns a `permissionDecisionReason` pointing at the
python-venv-manager skill. Calls through a venv's own interpreter (full path
or a `$PYTHON_BIN`-style variable) are unaffected — only bare invocations of
the system binaries are blocked.
