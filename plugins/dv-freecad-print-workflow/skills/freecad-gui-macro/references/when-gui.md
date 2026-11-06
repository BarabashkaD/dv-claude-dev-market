# GUI macro: details

Defaults only; a project may override numbers.

## Empty files and empty properties

- Never save an FCStd for a human from headless: no `GuiDocument.xml`, the file opens empty.
- Headless-side rules (explicit `Visibility`, `ViewObject` may be `None`, `optimalBoundingBox`, `Part.getShape(..., transform=True)` for links, `shape.copy()` before meshing) are owned by `freecad-headless-analysis`; follow them. The template's `snapshot()` already uses `Part.getShape`.
- After saving, reopen and compare: object count, visible objects, shapes (faces, volume), mesh if any, and a snapshot. The template does this in `snapshot()` and `verify()`.

## Comparing two FCStd files (before/after)

An FCStd is a zip.

1. Compare the member list and the content of each member that should not change.
2. Do not map objects by member file name: shape files are renumbered at every save. Map objects by object name, and for colors and visibility through `GuiDocument.xml` (its view-provider entries are keyed by object name).
3. Compare colors, transparency and visibility per mapped object, and shapes by facts (faces, volume) or an xor volume, not by bytes.
4. `Document.xml` differs in timestamps and ids; compare what matters, not the whole file.

## Replacing a shape in a copy of an accepted assembly

Work on a copy. Assign the new shape to the object and save without `recompute()`: a recompute rebuilds dependent history items and may change accepted geometry. Then reopen and verify counts and shape facts. If a recompute is truly needed, say why and check the dependents afterwards.

## Qt notes

- Activation: find the `QMdiSubWindow` of the document in `QMdiArea.subWindowList()` by title prefix (`"<name or label> : "`, titles look like `Name : 1[*]`), `QMdiArea.setActiveSubWindow(...)`, `processEvents()`, check `Gui.ActiveDocument.Document.Name`, then use `Gui.ActiveDocument.ActiveView`. The view object from `mdiViewsOfType` has no `parentWidget`; do not walk widgets from it.
- `view.saveImage(path, width, height, "Current")` renders the 3D scene; call `fitAll()` first. A widget grab of the main window shows black for the 3D area.
- Do not run long loops inside a timer callback: the in-macro watchdog is a timer too and cannot fire while the event loop is blocked. That is why the external watchdog by PID stays mandatory.

## If the process hangs

1. Read the JSON log first; it may already say why.
2. No documents open: terminate by PID (plain terminate), record the PID, the time and the last log step.
3. Unsaved data in the window: do not end it; report to the coordinator.
4. Fix `finish()` or the macro, not the watchdog.
