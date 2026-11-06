#!/usr/bin/env bash
# fc-quiet.sh <script.py>
# Run a FreeCAD headless script quietly.
#   - launcher: $FREECAD_LAUNCHER, else `freecadcmd` from PATH (warning on stderr)
#   - drops the startup banner, "( 50 %)" progress lines and empty lines; passes every other line
#   - stdin of the launcher is /dev/null (freecadcmd may otherwise wait for input)
#   - exit code is the launcher's exit code
#   - on TERM/INT/HUP the launcher and all its descendants are terminated (exit 128+signal)
# Portable bash (macOS and Linux): no setsid, no timeout. Needs pgrep, awk, mkfifo.
set -u

if [ $# -lt 1 ]; then
  echo "usage: fc-quiet.sh <script.py>" >&2
  exit 2
fi

if [ -n "${FREECAD_LAUNCHER:-}" ]; then
  launcher="$FREECAD_LAUNCHER"
else
  launcher="freecadcmd"
  echo "fc-quiet.sh: warning: FREECAD_LAUNCHER is not set, using freecadcmd from PATH" >&2
fi

if ! command -v "$launcher" >/dev/null 2>&1; then
  echo "fc-quiet.sh: launcher not found: $launcher" >&2
  exit 127
fi

tmp="$(mktemp -d)" || exit 2
mkfifo "$tmp/out" || exit 2
lpid=""; fpid=""

descendants() {  # print all descendant pids of $1 (depth first)
  local c
  for c in $(pgrep -P "$1" 2>/dev/null); do
    descendants "$c"
    echo "$c"
  done
}

kill_tree() {
  local p all
  [ -n "$lpid" ] || return 0
  all="$(descendants "$lpid") $lpid"
  kill -TERM $all 2>/dev/null
  sleep 0.2
  for p in $all; do kill -0 "$p" 2>/dev/null && kill -KILL "$p" 2>/dev/null; done
  return 0
}

on_signal() {  # $1 = signal number
  trap '' TERM INT HUP
  kill_tree
  [ -n "$fpid" ] && wait "$fpid" 2>/dev/null
  rm -rf "$tmp"
  exit $((128 + $1))
}
trap 'on_signal 15' TERM
trap 'on_signal 2' INT
trap 'on_signal 1' HUP

# Filter: banner (3 known lines), "(NN %)" progress, empty lines. Flush every line.
awk '
  /^[[:space:]]*$/ { next }
  /^[[:space:]]*\([[:space:]]*[0-9]+[[:space:]]*%[[:space:]]*\)[[:space:]]*$/ { next }
  /^FreeCAD [0-9][0-9.]*, Libs:/ { next }
  /^\(C\) [0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9] FreeCAD contributors/ { next }
  /^FreeCAD is free and open-source software/ { next }
  { print; fflush() }
' < "$tmp/out" &
fpid=$!

"$launcher" "$@" < /dev/null > "$tmp/out" 2>&1 &
lpid=$!
wait "$lpid"
rc=$?
wait "$fpid" 2>/dev/null
rm -rf "$tmp"
exit "$rc"
