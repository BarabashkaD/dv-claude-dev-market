---
name: freecad-mcp-operations
description: Use the existing FreeCAD MCP bridge only when the user's LIVE FreeCAD window is needed - the user's current selection, an open unsaved document, highlighting or inspecting objects in their window as you go, showing them a result - plus bridge health checks and recovery from a stuck GUI call. Not for geometry edits (except small changes the user asks for in their open document), checks, meshes, collisions, long or heavy operations (headless, see freecad-headless-analysis and freecad-zone-edit) and not for saving an FCStd a person will open (see freecad-gui-macro). Does not install or configure CAD servers.
license: Apache-2.0
---

> Modified in 2.0.0 (adapted; see [LICENSE](LICENSE), Apache-2.0 §4b): narrowed to the live-window role; the earlier "MCP-preferred" policy is withdrawn. History: [provenance](references/provenance.md).

# FreeCAD MCP: the user's live window only

The bridge works inside one shared FreeCAD window. A call runs on that window's GUI thread: it blocks the user, a long call freezes the interface, it has no PID of its own to watch or end, its code does not stay as a file, and its full answer (by default with a screenshot) lands in the agent's context. So MCP is used only for what needs the live window. Everything else goes elsewhere.

| Task | Way |
|---|---|
| Geometry edits, booleans, zones, guards, checks, meshes, collisions, sections, measurements | headless script: `freecad-zone-edit`, `freecad-headless-analysis` |
| Saving an FCStd a person will open, colors, visibility, camera, acceptance snapshot | separate GUI-macro run: `freecad-gui-macro` |
| The user's selection, their open unsaved document, highlight or inspect as you go, show them | **MCP (this skill)** |

This skill adds no MCP server, installer, launcher, autostart behaviour or printer control. An installed skill is not execution permission: the current task's authorization governs.

## One window, one user of it

- The window and the bridge are one resource: only one worker uses them at a time, by the coordinator's permission. Subagents do not use the user's window unless the coordinator assigned it.
- If the freecad-mcp add-on's `auto_start_rpc` is on (default port 9875), every GUI process starts the MCP server. A separate GUI-macro run therefore cannot overlap a live MCP session: run macros only on a profile copy with autostart off, after the user's window is closed (`freecad-gui-macro`).
- The bridge may start its own window on demand. Before any GUI call, find out whose window answers (`get_rpc_status()` does not open a window).
- Run limits: `guarding-autonomous-runs` (plugin dv-agent-controller).

## Reference contract and version

The documented reference is FreeCAD MCP 0.1.27: pinned [execution contract](https://github.com/neka-nat/freecad-mcp/blob/78bf0230a03324b56c9a0b7f55150fb5be2a0d42/docs/execution.md), [tool contract](https://github.com/neka-nat/freecad-mcp/blob/78bf0230a03324b56c9a0b7f55150fb5be2a0d42/docs/tools.md) and [server source](https://github.com/neka-nat/freecad-mcp/blob/78bf0230a03324b56c9a0b7f55150fb5be2a0d42/src/freecad_mcp/server.py). It does not prove which bridge is installed locally. Before use, check the actual tool schemas, bridge health and reported version; if they differ, report the mismatch and use only what the installed bridge supports.

## Health, discovery and document ownership

- `get_rpc_status()` is the GUI-independent health and version probe; use it first. `list_documents()` uses GUI dispatch and is not a health probe.
- Discover the exposed tools before choosing commands; report missing ones.
- Identify the intended document by name and exact object names, types and placements. The active document alone does not prove which document the task is about. Preserve the user's unsaved work.

## Live-window operations

- `get_objects` / `get_object`: read the open document, including its unsaved state.
- `execute_code(code, include_screenshot=False, ...)`: short calls only, such as reading the user's selection (`FreeCADGui.Selection.getSelectionEx()`), highlighting, setting a view. Pass `include_screenshot=False` unless the picture is for the user.
- `get_view(view_name, focus_object=...)`: show something to the user. A picture is for the person, never the way to analyse the model; measure by numbers headless.
- `reload_document(doc_name)`: reopen a saved document, saved by the user or by a GUI-macro run. A headless script never writes the user's FCStd (it would open empty); it writes BREP/STEP. Reconcile unsaved work first.
- Write into the user's document only when they asked for it: small, in a transaction, one change at a time. Code that matters as evidence is saved as a file in the round folder, not only sent as a string.

## Not through MCP

- Long or heavy operations, booleans on a whole body, `execute_code_async` jobs: they run in the window's process, cannot be cancelled once started (check the bridge's tool schema; the 0.1.27 tool list has no cancel call), and a native crash takes the window with its unsaved documents. Use a headless script with its own PID and watchdog.
- `execute_code_headless` starts a separate `freecadcmd`, but gives no PID, no streaming progress and only a hard timeout (default 600 s). Prefer the quiet wrapper `../freecad-headless-analysis/scripts/fc-quiet.sh`. If it is used anyway, set `timeout` explicitly to at most 300 s.
- Saving an FCStd for a person from headless (no `GuiDocument.xml`, it opens empty): use `freecad-gui-macro`.

## Recovery from a stuck call

Queue expiry before a GUI operation starts cancels it; expiry after it started does not stop a mutation already running. On `GUI_DISPATCH_STUCK`: check `get_rpc_status()` and `get_async_status()`, inspect document state, then report to the coordinator. Never retry a possibly executed mutation blindly, never duplicate features, and never kill the user's window or start a competing profile to hide the uncertainty.

## Boundaries

Report performed, failed and NOT RUN checks separately. This skill does not authorize changing unrelated projects, installing software, changing MCP configuration, publishing or printing. Stage sequence and round rules: `cad-print-workflow`.
