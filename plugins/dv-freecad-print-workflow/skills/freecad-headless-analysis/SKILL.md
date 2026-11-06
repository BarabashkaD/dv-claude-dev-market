---
name: freecad-headless-analysis
description: Analyse a FreeCAD model by numbers in headless runs (freecadcmd), not by pictures. Use for measuring geometry, clearances, intersections, volumes, mesh checks, cross-sections to SVG, change checks before/after, collision checks between exported parts, and for running FreeCAD scripts quietly with the bundled fc-quiet.sh wrapper (RESULT-only output). Not for building or editing geometry (see freecad-zone-edit), not for GUI or screenshot work (see freecad-gui-macro), not for live-window work through MCP.
---

# FreeCAD headless analysis by numbers

Analyse a model with FreeCAD 1.1.4 built-in tools in a headless run (`freecadcmd`): `common`, `distToShape`, `slice`, `check`, mass properties, meshes. Numbers decide; images do not. A picture is for showing a result to a person and for the GUI gate (the file opens and looks right), never the way the model analyses geometry.

Numbers in this skill are defaults; a project may override them.

## Do not loop

If there is no fitting built-in tool, or the task is unclear without an image, do not hunt for a workaround for hours. Stop, tell the coordinator or the user what the problem is, and propose a better or faster way (including an image, if that is truly simpler). Then ask and wait for the decision. Run limits, the flexible 5-minute rule and the 30-minute stop are in `guarding-autonomous-runs`; do not restate them here.

## Running scripts

- Run `scripts/fc-quiet.sh <script.py>`. The path is relative to the directory of this SKILL.md; resolve it to an absolute path before running. It needs bash, `pgrep` and `mkfifo` (macOS and Linux only). It reads the launcher from `$FREECAD_LAUNCHER` (else `freecadcmd` from PATH, with a warning), drops the banner, `(NN %)` progress and empty lines, keeps the launcher's exit code, and on TERM/INT/HUP ends the launcher and its child processes. Details: [references/quiet-wrapper.md](references/quiet-wrapper.md).
- `freecadcmd` treats argv as files, so pass parameters through environment variables.
- A script prints one line to stdout, `RESULT {json}`, and nothing else. On failure it prints `RESULT {"error": ...}`. Read the result by that line.
- **Heartbeat, not stdout:** a long script appends lines `PROGRESS <n>/<N> <label>` to a log file in the round folder (for example `$ROUND_DIR/progress.log`), never to stdout; the watcher tails the log. Default silent interval is 60 s. A single long OCC call cannot print: judge it by growing CPU time plus the 5-minute limit. Fragment: [references/quiet-wrapper.md](references/quiet-wrapper.md#heartbeat).
- Run limits: `guarding-autonomous-runs` (plugin dv-agent-controller). In short: 5 minutes per run by default; stop at 60 s without a heartbeat or on warnings; localize or divide; about 30 minutes without a first cause means stop and report.
- Never save an FCStd for a human from a headless run (no view data, the file opens empty). Save files for people from a GUI-macro run (`freecad-gui-macro`).
- Use a throwaway or copied profile for experiments (`FREECAD_USER_HOME`, `FREECAD_USER_DATA`, `FREECAD_USER_TEMP`), not the user's real one.
- Analysis in headless does not need the user's open window. Use MCP only when the live window is needed (user's selection, an open unsaved document, showing something); see `freecad-mcp-operations`.

## Rules for scripts

These shared headless rules live here once; other skills link to them.

1. **Guard before use.** Check `Shape.isNull()`, that there are solids, that the BoundBox is valid; `ViewObject` may be `None` in headless. Objects made without GUI need `Visibility = True` set explicitly.
2. **Bounding box:** use `shape.optimalBoundingBox()`. The plain `BoundBox` of BSpline shapes is loose and misleads clearances.
3. **Links and parts:** take the shape of an `App::Link` or `App::Part` with `Part.getShape(obj, "", transform=True)` so the placement is applied.
4. **Mesh from a shape:** `MeshPart.meshFromShape(shape.copy(), LinearDeflection=0.015, AngularDeflection=0.08, Relative=False)`. Always mesh a copy (`shape.copy()`), not the original. For sensitivity checks vary around the defaults (0.0145..0.0155 and 0.075..0.085).
5. **Change checks (before/after):** compare volume, area and counts; the default tolerance is 0.001 % of the expected change (dV/dA), floor 1e-3 mm3 / mm2, never of the whole body (as in `freecad-zone-edit`). Take "before" values from the recorded previous result.
   Edge tolerance default, "deviation x 1.1, cap 5e-4": the BRep tolerance of an edge, face or vertex inflated by booleans is lowered to its measured geometric deviation x 1.1, never above 5e-4 mm (`shape.limitTolerance(0, 5e-4)`, read `Edge.Tolerance`). It does not close an open mesh by itself: fix a fragile corner in the geometry (see `freecad-zone-edit`, references/guards.md, "BRep tolerance after booleans").
6. **Heavy operations are local.** `section`, `common`, `distToShape`, `check`, `ancestorsOfType` on a whole body or assembly can run for minutes or hang. Localize by default: cut both operands with a box of about 20 mm around the area of interest (`part.common(box)`) and run the operation on the pieces; or split into zones, groups of faces or single parts and combine the results (for example xor per zone). A face loop is faster than `mesh.Facets[i]` indexing.
7. **Verify the artifact, not the answer.** After saving, reopen: object count, visible objects, shapes (faces, volume), mesh. Compare FCStd contents by zip file, and colors or visibility by object mapping in `GuiDocument.xml`, not by file name (names are renumbered on each save).
8. **Recompute:** in a copy of an accepted assembly, replace an object's shape without calling `recompute` when other objects depend on it in the history; a recompute would rebuild them and change unrelated geometry.
9. Harmless startup noise (3Dconnexion messages, `QtCore not defined` from Assembly in headless) is not an error.

## Collisions

Check collisions between exported parts, one pair or group at a time, not on a whole assembly in one operation. What to check, which pairs and how much clearance counts is set by the project (its interference and clearance spec). Method and the local box: [references/collision-scope.md](references/collision-scope.md).

## Sections

Recommended: `Shape.slice` plus your own SVG. It is headless, takes milliseconds on small parts, and does not depend on TechDraw or GUI. On big bodies localize with a box first (rule 6). A working script with env-var parameters, exact bounding box, area from faces, standard views and mm dimension labels: [references/section_svg_example.py](references/section_svg_example.py). It was tested only on a small prismatic part.

- Built-in dimensions: TechDraw `DrawViewSection` with a `DrawViewDimension` gives a real dimension, but only in the page DXF (`TechDraw.writeDXFPage`), not in headless SVG. Use it when a DXF with dimensions is acceptable.
- A TechDraw page exported as SVG needs a GUI run (`TechDrawGui` crashes headless): use `freecad-gui-macro`.
- `TechDraw.projectToSVG` and Draft `get_svg` give outlines without dimensions, with rotated axes; treat them as fallbacks.
- An offscreen 3D snapshot is not available on macOS without a window session (the GL context cannot be created). For checks use numbers and section outlines; for showing a person use a GUI-macro snapshot.
- Sketch drafts: SVG is clearer than a snapshot.

## Defaults summary

Change tolerance 0.001 %; mesh 0.015 / 0.08 / `Relative=False`; edge tolerance deviation x 1.1, cap 5e-4 (BRep tolerance, rule 5); local box about 20 mm; SVG chord deflection 0.01 mm. Projects may override any of these.
