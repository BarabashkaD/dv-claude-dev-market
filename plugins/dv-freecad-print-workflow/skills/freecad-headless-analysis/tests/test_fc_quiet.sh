#!/usr/bin/env bash
# Tests for scripts/fc-quiet.sh with a fake launcher (no FreeCAD needed).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
WRAP="$HERE/../scripts/fc-quiet.sh"
TMP="$(mktemp -d)"
trap '[ -n "${BG:-}" ] && kill "$BG" 2>/dev/null; rm -rf "$TMP"' EXIT
fail=0
check() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1: expected [$3] got [$2]"; fail=1; fi; }

# Case 1: banner, progress and empty lines dropped; RESULT kept; exit code kept.
cat > "$TMP/fake" <<'EOS'
#!/usr/bin/env bash
cat >/dev/null   # would hang if stdin were not /dev/null
echo "FreeCAD 1.1.4, Libs: 1.1.4R20260928 (Git shallow)"
echo "(C) 2001-2026 FreeCAD contributors"
echo "FreeCAD is free and open-source software licensed under the terms of LGPL2+ license."
echo ""
echo "( 50 %)"
echo "(100 %)"
echo "RESULT {\"ok\":1}"
exit 3
EOS
chmod +x "$TMP/fake"
FREECAD_LAUNCHER="$TMP/fake" "$WRAP" script.py > "$TMP/out" 2> "$TMP/err" < /dev/null
rc=$?
check "output only RESULT" "$(cat "$TMP/out")" 'RESULT {"ok":1}'
check "exit code kept" "$rc" "3"
check "no warning with FREECAD_LAUNCHER" "$(cat "$TMP/err")" ""

# Case 2: fallback to freecadcmd from PATH warns on stderr.
mkdir "$TMP/bin"; cp "$TMP/fake" "$TMP/bin/freecadcmd"
env -u FREECAD_LAUNCHER PATH="$TMP/bin:$PATH" "$WRAP" script.py > "$TMP/out" 2> "$TMP/err" < /dev/null
check "fallback output" "$(cat "$TMP/out")" 'RESULT {"ok":1}'
case "$(cat "$TMP/err")" in *FREECAD_LAUNCHER*) echo "PASS fallback warns"; ;; *) echo "FAIL fallback warns"; fail=1 ;; esac

# Case 2b: missing launcher -> message on stderr, exit 127.
FREECAD_LAUNCHER="$TMP/does-not-exist" "$WRAP" script.py > "$TMP/out" 2> "$TMP/err" < /dev/null
check "missing launcher exit" "$?" "127"
case "$(cat "$TMP/err")" in *"not found"*) echo "PASS missing launcher message" ;; *) echo "FAIL missing launcher message"; fail=1 ;; esac

# Case 3: TERM to the wrapper kills the launcher's child (no orphan).
cat > "$TMP/slow" <<EOS
#!/usr/bin/env bash
sleep 300 &
echo \$! > "$TMP/child.pid"
wait
EOS
chmod +x "$TMP/slow"
FREECAD_LAUNCHER="$TMP/slow" "$WRAP" script.py > /dev/null 2>&1 < /dev/null &
BG=$!
for _ in $(seq 1 50); do [ -s "$TMP/child.pid" ] && break; sleep 0.1; done
child="$(cat "$TMP/child.pid" 2>/dev/null)"
if [ -z "$child" ]; then echo "FAIL child did not start"; fail=1; else
  kill -TERM "$BG"; wait "$BG" 2>/dev/null; wrc=$?
  sleep 0.3
  if kill -0 "$child" 2>/dev/null; then echo "FAIL orphan child $child left"; kill "$child"; fail=1
  else echo "PASS TERM killed child tree"; fi
  check "wrapper exit on TERM" "$wrc" "143"
fi
exit $fail
