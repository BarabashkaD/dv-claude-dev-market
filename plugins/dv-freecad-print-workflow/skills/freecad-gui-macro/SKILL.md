---
name: freecad-gui-macro
description: Run a FreeCAD 1.1.4 macro in a separate GUI process, safely, and decide when a GUI run is needed at all. Use to save an FCStd a person will open (headless saves lose GuiDocument.xml), set visibility, colors or camera, take a real window snapshot, simulate an Assembly, export with colors, or compare FCStd files. Ships a macro template. Not for geometry edits, checks, meshes or measurements (freecad-headless-analysis); not for the user's live window (freecad-mcp-operations).
---

# FreeCAD GUI macro: when, and how to run it safely

A GUI run is the exception. Geometry, checks and numbers go to headless scripts (`freecad-headless-analysis`, `freecad-zone-edit`). Use a separate GUI process only for what needs view data. Run limits and the stop rules: `guarding-autonomous-runs` (plugin dv-agent-controller). Do not restate them here. Numbers in this skill are defaults; a project may override them.

## When a GUI run is needed

- Saving an FCStd that a person will open. A headless save drops `GuiDocument.xml`, so the file opens "empty". Never save such a file from a headless run.
- Visibility, colors, transparency, camera; export with colors.
- Restoring the display after a headless save.
- A snapshot of the real window for acceptance, and the GUI gate: the file opens and looks right.
- Simulation and animation of an Assembly.

Exception: highlighting or showing something in the user's own live window is MCP, not a GUI-macro run (see `freecad-mcp-operations`).

## When it is not needed (even if it seems so)

Section and drawing drafts (SVG, headless), checks (`check`, xor, mass properties), meshes, collisions, measurements, clearances, shape export without colors (STL, BREP, STEP), and any long or heavy operation: those need their own process with a PID and a watchdog, headless.

## One GUI at a time

The GUI is one shared resource. GUI-macro runs go strictly one after another: the profile writes its configuration at exit, and recovery files from a previous run get in the way of the next one. Subagents do not launch the GUI; the coordinator runs the GUI gate. A GUI-macro run and a live MCP session cannot overlap (see the launch conditions below).

## Before launch

1. `ast.parse` the macro. A syntax error leaves an empty window that must then be ended by hand.
2. `pgrep -f FreeCAD.app` (on other platforms, the FreeCAD process name) must print nothing. If the user's window is open, ask them to close it and wait. Do not launch next to it.
3. Prepare a temporary copy of the profile (config and data folders). Never change the original.
4. In the copy's `freecad_mcp_settings.json` (data folder) set `"auto_start_rpc": false`. If the freecad-mcp add-on's `auto_start_rpc` is on (default port 9875), the macro's process would take the MCP port and break the user's MCP session, or be refused. The copy still holds the auth token: blank the token value in the copy (autostart is off, so it is unused), never print or copy it anywhere (logs, reports, chat, repo).
5. Search the copy's `user.cfg` and `system.cfg` for absolute paths into the original profile folder. If any exist, rewrite them to the copy, in the copy only. Stale "last used folder" values are harmless.
6. Read the launcher from `$FREECAD_GUI_LAUNCHER` (the FreeCAD GUI executable or a wrapper script). A wrapper must `exec` FreeCAD as its last step; otherwise `$!` is the wrapper's PID and FreeCAD is orphaned when the watchdog ends the wrapper. Do not hard-code its path.

## Launch

Put the output folder outside the profile copy, because the copy is deleted at the end. Point the process at the copy with environment variables and flags, pass the macro (resolve its path to an absolute one from this skill's directory first) as the file argument:

```
OUT="$(mktemp -d)"   # outside $COPY
FREECAD_USER_HOME="$COPY" FREECAD_USER_DATA="$COPY/data" \
FREECAD_USER_TEMP="$COPY/tmp" GUI_MACRO_OUT_DIR="$OUT" \
"$FREECAD_GUI_LAUNCHER" --user-cfg "$COPY/config/user.cfg" \
  --system-cfg "$COPY/config/system.cfg" "$MACRO" </dev/null >"$OUT/gui.log" 2>&1 &
PID=$!
```

Adjust the layout to the profile's actual folders. External watchdog (the platform may have no `timeout`), default limit 120 s, launcher side only:

```
for i in $(seq 120); do kill -0 "$PID" 2>/dev/null || break; sleep 1; done
if kill -0 "$PID" 2>/dev/null; then   # still alive: record, then end by PID
  echo "watchdog: ending PID $PID after 120 s" >>"$OUT/watchdog.txt"
  kill -TERM "$PID"; sleep 5
  # KILL only after the operator confirmed this window holds no documents or unsaved data; otherwise stop here and ask
  kill -0 "$PID" 2>/dev/null && kill -KILL "$PID"
fi
```

Use the forced step only for a window with no documents and no unsaved data; otherwise stop at TERM and report. The macro has its own shorter in-macro watchdog that writes the log and exits normally; it fires only at event-loop points, so the external one stays mandatory. The process must end by itself. After the run, copy what you need out of the output folder (it is already outside the copy), then delete the profile copy (it holds the token).

## The macro

Start from `assets/gui_macro_template.py` (path relative to the directory of this SKILL.md); edit `modify()` and `verify()`.

- Environment variables (all optional): `GUI_MACRO_INPUT` (FCStd to copy and open; empty means a new empty document), `GUI_MACRO_OUT_DIR` (output folder; default a new temp folder), `GUI_MACRO_LOG_JSON` (log path; default `<OUT_DIR>/result.json`), `GUI_MACRO_TIMEOUT` (in-macro watchdog, seconds, default 100), `GUI_MACRO_ALLOW_XLINKS` (`1` to open an input with external links).
- Inputs with external links (accepted assemblies): a lone copy breaks relative links. The template refuses them; copy the dependent files together into the same relative layout, then set `GUI_MACRO_ALLOW_XLINKS=1`.
- Interface: `activate(doc) -> view` (through the MDI area), `run()`, `finish()` (closes its own documents, then the main window), `OUT_DIR` and `LOG_JSON` from environment variables.
- Start through `QtCore.QTimer.singleShot` after the event loop is running, not at import.
- Flow: open a COPY of the input (or a new empty document when no input is given), modify, save, close, reopen, verify, `saveImage` from the view, write the JSON log, exit normally.
- Results and errors go to the JSON log (`ok`, steps, `error`). On error the macro still calls `finish()`, so no empty window stays.
- Exit is normal: close own documents, then the main window. Only the PID fallback above ends a hung process.

## Qt and API pitfalls (1.1.4)

- There is no `Gui.activateDocument`. Activate through the MDI area: find the document's sub-window and `setActiveSubWindow`.
- Call `QApplication.processEvents()` after changes.
- Take PySide from the FreeCAD bundle (`from PySide import ...`), not from a system install.
- A window grab does not capture OpenGL content. Take the image from the 3D view with `view.saveImage(...)`.
- Harmless startup messages are not errors: 3Dconnexion warnings; `QtCore not defined` from Assembly in headless runs.
- Before `recompute`, think. In a copy of an accepted assembly, replace shapes without recompute: objects may have dependent history items that a recompute would rebuild.

Details, empty-file and empty-property rules, and the FCStd comparison recipe: [references/when-gui.md](references/when-gui.md).

## After the run (check the artifact, not the answer)

Read the JSON log: `ok: true`, the expected PNG exists and is non-empty, the saved file reopens, and object count, visible objects and shapes (faces, volume) match. "Success" printed by the macro is not proof. To show the user a file, open it the way the user launches the app (their own launcher and profile), not through the temporary copy.
