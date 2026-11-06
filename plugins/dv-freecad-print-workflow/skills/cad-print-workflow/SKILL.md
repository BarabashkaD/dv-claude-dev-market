---
name: cad-print-workflow
description: Coordinate a FreeCAD-to-3D-print project: stages, design and refinement rounds, user decisions, choosing headless script, GUI-macro run or MCP live window, showing results before checks or an authorized autonomous series to a candidate, evidence statuses (NOT RUN, stale), round closure, CAD-ready gate, hand-over to Bambu Studio. Use for multi-stage CAD-to-print work or to decide whether a print finding needs a new design round. Not the technique itself; sibling skills hold that.
---

# Design first, prepare printing second

Complete the current FreeCAD design round before entering Bambu Studio. Design with the intended printer and process in mind, but do not slice after every edit. This skill sets the stage sequence; the linked skills supply the techniques. Scale records to the task: a simple part needs no project bureaucracy. Numbers in these skills are defaults; a project may override them.

## Three ways of working

| Need | Way | Skill |
|---|---|---|
| Geometry edits, checks, meshes, collisions, sections, measurements | headless script (`freecadcmd` through the quiet wrapper, `RESULT {json}` only) | `freecad-zone-edit`, `freecad-headless-analysis` |
| An FCStd a person will open, visibility/colors/camera, window snapshot for acceptance, Assembly animation | separate GUI process with a macro, its own PID | `freecad-gui-macro` |
| The user's selection, an open unsaved document, highlighting or inspecting in their window as you go, showing them something | MCP into the user's live window | `freecad-mcp-operations` |

- Headless is the default for anything heavy or long: it has its own process, a PID, a watchdog and a script file that stays as evidence.
- A feature-tree edit of a parametric FCStd that a person will open is applied and saved in a `freecad-gui-macro` run (its modify step). Headless alone delivers BREP/STEP, or edits a copy that a GUI-macro run then opens, checks and saves.
- The GUI is one shared resource. A GUI-macro run and a live MCP session never overlap (the profile autostarts the MCP server on one port); GUI runs go one at a time and only the coordinator starts them.
- Run limits: `guarding-autonomous-runs` (plugin dv-agent-controller).
- Analyse the model by numbers, not by pictures. Pictures are for showing a person and for the GUI gate.
- An installed skill is guidance, not permission. Execution, installation, configuration changes, publishing and printing follow the current task's authorization.

## Verify current methods

Before adopting a new construction method or tool, follow [current documentation and capability checks](references/current-documentation.md): record the installed versions (FreeCAD 1.1.4 here, OpenCASCADE, bridge), consult version-relevant official guidance, and keep application capability separate from what a bridge exposes. Reuse recorded evidence for routine repetition; recheck on version or method changes or unexpected failures. KiCad checks apply only to actual ECAD work, not to a supplied valid STEP reference.

## CAD design round

Read the current project, accepted decisions and authoritative model before asking for information. Establish material, printer and build envelope, nozzle (0.4 mm by default; confirm the actual setup), surface, fit and strength goals early. FDM minimum sizes, default fits and build order for any printed part: [FDM defaults](../freecad-rib-engineering/references/fdm-defaults.md). Do not silently substitute materials: a change can alter fits, flexible joints and structural assumptions.

Resolve structural, engineering and visual choices in FreeCAD: arrangement, part boundaries, walls, reinforcement, hardware and retention, motion and access. Check the real dimensions and envelopes of purchased components before modelling around them. Consider print orientation, anisotropy, overhangs, support removal and assembly without claiming slicer verification. Keep reference assemblies and their coordinates separate from manufactured parts.

Use named driving dimensions, stable references, native high-level features and reusable prototypes in parametric work. Keep distinct manufactured parts distinct and test expected part counts explicitly. Preserve a baseline before consequential edits; serialize CAD writes.

### Decisions and batches

Keep one short decision record for the project; use the [project-record template](references/project-record-template.md) where useful. Record decision, reason or source, status and affected parts. Reuse answered questions and delegated authority.

Bundle related open questions with evidence, a recommendation and consequences. Consult on design direction and on technical alternatives that are comparably suitable. Choose routine implementation yourself within the agreed intent; do not ask the user to choose unexplained alternatives or to reconfirm every edit. Silence is not approval for a blocked decision; continue with independent work.

## Showing results and autonomous series

- **Default:** show the result (a short view or section plus the key numbers) to the user before running the check stage, unless the user granted autonomy. If the location or meaning of a remark is unclear, confirm your interpretation before editing, for example by highlighting the region in their window through MCP; do not ask by default before every edit.
- **Autonomous series:** if the user explicitly allowed autonomous work, run the series to the end and hand over a **candidate**: result, numbers, checks passed, checks NOT RUN, assumptions. Only the user accepts a new version. Manufacturing, printing and publishing need direct permission even inside a series. On a block, stop and report.
- Coordinator and worker split, verify-the-artifact and candidate rules: `guarding-autonomous-runs`.

## Local refinement rounds

When the model is accepted and the user is reviewing localized remarks, work in a refinement round rather than restarting design. A new remark does not reopen global design or trigger a full audit.

- At the start, keep one recoverable baseline and name the accepted revision and scope. Make the smallest edit that addresses each remark; leave unrelated features and decisions untouched.
- Finished solids, imported STEP/BRep bodies and repeated identical features: edit by the zone method with its guards (`freecad-zone-edit`).
- Recompute: in a live parametric model, recompute what the edit requires and check the affected features. In a copy of an accepted assembly, replace the shape without `recompute`; a recompute rebuilds dependent history and can change accepted geometry.
- After each edit, run the local checks for the affected region and interfaces (zone guards, clearances, mesh). Keep a short running list of changes, local results and deferred checks.
- A geometry change makes earlier dependent evidence stale (exports, meshes, collisions, slices, snapshots): mark it, and re-run or report it as NOT RUN. A deferred or unperformed check is NOT RUN, never PASS.
- Until the user closes the round (any clear wording, such as "all remarks are done, check everything"), defer the full check, parameter sweeps, complete export sets and slicing. A request for a final export earlier changes the scope: run the validation that deliverable needs.
- On closure, run one full check of the accumulated result, divided into parts that fit the run limits where needed, including the whole-body print mesh once (at the default deflection; the neighbouring values stay per zone). `check(True)` of the whole body only when allowed; collisions only against exported physical parts. Regenerate deliverables only for the validated revision.

If a local edit exposes a global structural issue or would change accepted architecture, layout, load paths or unrelated parts, stop that edit, explain the impact and the broader scope, and get direction unless that authority was delegated. Do not hide blocking local failures in the deferred list.

## CAD-ready gate

Move to print preparation when the substantial design decisions are settled, no open question materially changes the construction, the intended checks have passed, and a named source revision plus a matching export exists. Do not call an incomplete design CAD-ready just because the export succeeded.

Relevant checks: valid expected solids, dimensions and clearances, fit, motion and access, closed print mesh. For a parametrically reusable design, exercise representative values on copies, then restore the nominal model and re-verify it; a shape check alone does not prove parametrization, and a selected sweep is not proof over the whole range. Slicer checks may remain NOT RUN at CAD readiness; physical validation that was not done stays an explicit open qualification.

## Print preparation and return

Only now prepare the accepted design in Bambu Studio (`bambu-print-preparation`). Keep the link between CAD revision, export, Bambu project, settings and results. A settings-only change stays in print preparation. Every proposed CAD change at this stage needs a specific print finding and an impact assessment.

A local correction that preserves accepted function, appearance, interfaces, layout and load paths is edited in FreeCAD and rechecked without reopening the whole design; a small dimension can still matter if it changes a fit or a latch. For substantial changes, collect the findings and alternatives, get the user's direction on reopening design, pause slicing, run a FreeCAD-only round and return through the same gate. The slicer never becomes a parallel geometry source.

## Evidence and release

Use the [release-evidence template](references/release-evidence-template.md) where a reusable record helps. Statuses are PASS, FAIL, NOT RUN or NOT APPLICABLE with a reason; never write PASS for missing evidence.

- Check the artifact, not the answer: reopen the saved file, re-read the shape or mesh, compare the numbers.
- Check an export by importing it again and comparing it with the source (volume, area, bounding box, part count).
- Numeric checks cover every target part, not only the first one reported. Expected-failure regression cases are kept apart and never qualify a release.
- Record the FreeCAD and OpenCASCADE versions the checks ran with.
- After geometry changes, invalidate dependent export and slice evidence; after profile or orientation changes, invalidate affected slice evidence. CAD-ready, slice-reviewed and physically qualified are different statuses.
- Preparing a print package does not authorize sending it to a printer or publishing it.
