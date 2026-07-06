#!/usr/bin/env bash
# ensure_venv.sh <skill-name> [requirements-file | package ...]
#
# Prints the path to that skill's venv python interpreter on stdout.
# All other output (pip logs, venv creation logs) goes to stderr, so
# callers can safely do: PYTHON_BIN=$(ensure_venv.sh "some-skill" ...)
#
# If the venv already exists, this does nothing else — no package
# re-check, no pip re-run — and returns immediately. That's intentional:
# reuse across sessions/projects is the entire point of this script.
#
# Runs under any bash-compatible shell (Linux, macOS, WSL, Git Bash on
# Windows). Home directory, the python launcher (python3/python/py), and
# the venv layout (bin/ vs Scripts/) are all detected at runtime instead
# of assumed, so the same script works unmodified across platforms.
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: ensure_venv.sh <skill-name> [requirements-file | package ...]" >&2
  exit 1
fi

SKILL_NAME="$1"
shift

# Sanitize skill name for filesystem use (skill names may contain ':' or '/',
# e.g. "document-skills:pdf" or namespaced plugin skills).
SAFE_NAME=$(echo "$SKILL_NAME" | tr ':/ ' '---')

# $HOME is set by Linux, macOS, WSL, and Git Bash alike. $USERPROFILE is
# the fallback for the rare bash environment where it isn't (some MSYS
# setups on native Windows).
HOME_DIR="${HOME:-${USERPROFILE:-}}"
if [ -z "$HOME_DIR" ]; then
  echo "Could not determine home directory (neither \$HOME nor \$USERPROFILE is set)" >&2
  exit 1
fi

VENV_ROOT="${CLAUDE_VENV_ROOT:-$HOME_DIR/.claude/venvs}"
VENV_PATH="$VENV_ROOT/$SAFE_NAME"

# venv layout differs by platform: POSIX venvs put the interpreter under
# bin/, Windows venvs use Scripts/ with a .exe suffix. Check both rather
# than assuming one.
resolve_python_bin() {
  if [ -x "$VENV_PATH/bin/python" ]; then
    printf '%s' "$VENV_PATH/bin/python"
  elif [ -x "$VENV_PATH/Scripts/python.exe" ]; then
    printf '%s' "$VENV_PATH/Scripts/python.exe"
  fi
}

PYTHON_BIN=$(resolve_python_bin)

if [ -n "$PYTHON_BIN" ]; then
  # Already exists — trust it, skip everything else.
  echo "$PYTHON_BIN"
  exit 0
fi

# Prefer python3 (standard on Linux/macOS); fall back to python or the
# Windows py launcher, both common where python3 doesn't exist.
PYTHON_LAUNCHER=""
for candidate in python3 python "py -3"; do
  if command -v "${candidate%% *}" >/dev/null 2>&1; then
    PYTHON_LAUNCHER="$candidate"
    break
  fi
done
if [ -z "$PYTHON_LAUNCHER" ]; then
  echo "No python3/python/py interpreter found on PATH" >&2
  exit 1
fi

mkdir -p "$VENV_ROOT"
echo "Creating venv for '$SKILL_NAME' at $VENV_PATH" >&2
$PYTHON_LAUNCHER -m venv "$VENV_PATH"

PYTHON_BIN=$(resolve_python_bin)
if [ -z "$PYTHON_BIN" ]; then
  echo "venv creation reported success but no interpreter was found under bin/ or Scripts/" >&2
  exit 1
fi

PIP_BIN="$(dirname "$PYTHON_BIN")/pip"
[ -x "$PIP_BIN" ] || PIP_BIN="$(dirname "$PYTHON_BIN")/pip.exe"

"$PIP_BIN" install --quiet --upgrade pip >&2

if [ "$#" -gt 0 ]; then
  if [ -f "$1" ]; then
    echo "Installing from requirements file: $1" >&2
    "$PIP_BIN" install --quiet -r "$1" >&2
  else
    echo "Installing packages: $*" >&2
    "$PIP_BIN" install --quiet "$@" >&2
  fi
fi

echo "$PYTHON_BIN"
