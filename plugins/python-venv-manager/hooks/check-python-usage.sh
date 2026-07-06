#!/usr/bin/env bash
# PreToolUse hook (Bash matcher): blocks bare invocations of the system
# python3/python/pip3/pip and points the caller at ensure_venv.sh instead,
# so packages always land in a per-skill venv rather than system Python.
set -euo pipefail

input=$(cat)
command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')

if [ -z "$command" ]; then
  exit 0
fi

# Matches "python"/"python3"/"python3.x"/"pip"/"pip3" only when it sits in
# command position: bounded by whitespace, quotes, shell separators, or
# start/end of string. Punctuation like "-"/"."/"/" does NOT count as a
# boundary, so path segments (~/.claude/venvs/<skill>/bin/python3) and
# identifiers (python-venv-manager, pip-compile, pipx) are left alone.
if printf '%s' "$command" | grep -Eq '(^|[[:space:];&|()`$"])(python(3(\.[0-9]+)?)?|pip3?)([[:space:];&|()`$"]|$)'; then
  reason='Direct python3/pip invocation blocked. Invoke the python-venv-manager skill to get a per-skill venv interpreter (its SKILL.md explains how to locate scripts/ensure_venv.sh relative to that skill'\''s own reported base directory - do not assume a fixed install path), then call that interpreter (and its sibling pip) instead of system python3/pip.'
  jq -n --arg reason "$reason" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
  exit 0
fi

exit 0
