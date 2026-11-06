# fc-quiet.sh: quiet headless launcher

`scripts/fc-quiet.sh <script.py>` (in this skill's directory) runs a FreeCAD script headless and leaves only the useful lines. Parameters go to the script through environment variables, not argv.

## Requirements it meets

- **Launcher:** `$FREECAD_LAUNCHER` if set (full path to `freecadcmd`); otherwise `freecadcmd` from PATH and a warning on stderr. Never hard-code a path in a skill or script.
- **Filtered out:** the three-line startup banner, progress lines such as `( 50 %)`, and empty lines. Every other line is passed unchanged and flushed at once. Other tools' messages (for example STEP transfer statistics) are not hidden; read results by the `RESULT ` prefix.
- **stdin is `/dev/null`:** `freecadcmd` may wait for input otherwise and look like a hang. Do not rely on stdin from the wrapper.
- **Exit code** is the launcher's own code (not the filter's).
- **Signals:** on TERM, INT or HUP the wrapper ends the launcher and all of its descendants (TERM, then KILL for survivors) and exits with 128 plus the signal number. A run killed from outside therefore leaves no orphan FreeCAD process.
- **Missing launcher:** message on stderr, exit 127.
- **Portable:** plain bash plus `pgrep`, `awk`, `mkfifo` (macOS and Linux only); no `setsid` or `timeout` (macOS has neither by default).

## Usage

```
export FREECAD_LAUNCHER=/path/to/freecadcmd        # set once in the environment
scripts/fc-quiet.sh analysis.py | grep '^RESULT '
```

`freecadcmd` treats argv as files, so give parameters through environment variables.

For a time limit, use the agent runner's timeout or send TERM from a watchdog; the wrapper cleans up. Choosing the limit and when to stop is in `guarding-autonomous-runs`.

## Test

`bash tests/test_fc_quiet.sh` uses a fake launcher in a temp directory (no FreeCAD needed): output reduced to `RESULT`, exit code kept, PATH fallback warns, and TERM to the wrapper kills the launcher's child.

## Heartbeat

The wrapper output carries only `RESULT`. For progress, a long script appends lines to a log file in the round folder (never to stdout), and the watcher tails that file. Fragment:

```
import os
_LOG = os.path.join(os.environ.get("ROUND_DIR", "."), "progress.log")

def progress(n, total, label):
    with open(_LOG, "a", encoding="utf8") as f:
        f.write("PROGRESS %d/%d %s\n" % (n, total, label))
        f.flush()
        os.fsync(f.fileno())
```

Call it once per part, zone or face batch; the default silent interval is 60 s. One long OCC call (a boolean, `distToShape`) cannot emit heartbeats: judge it by growing CPU time and the run limit in `guarding-autonomous-runs`.
