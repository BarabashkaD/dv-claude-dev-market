---
name: bambu-print-preparation
description: Prepare a CAD-ready model for printing in Bambu Studio using the native UI or CLI - import and check the export, choose printer, nozzle, material, orientation and supports, slice, review layers, write the 3-line print recipe and classify print-driven corrections (settings-only, local geometry fix, new design round). Use after the CAD-ready gate of cad-print-workflow or to inspect an existing print project. Not a CAD design stage and not printer dispatch.
---

# Bambu Studio print preparation

Start after the current CAD design is ready, or when explicitly asked to inspect an existing print project. For unfinished design, use [cad-print-workflow](../cad-print-workflow/SKILL.md) rather than introducing repeated early slicing. This skill supplies operating guidance, not an MCP server, CLI wrapper, driver or guaranteed tool capability.

## Identify the real tools and inputs

Apply [current documentation and capability checks](../cad-print-workflow/references/current-documentation.md) when selecting a new method, encountering version changes or investigating an unexpected failure. Keep a concise version/source/conclusion record and reuse it for ordinary iterations.

Discover the installed Bambu Studio version and available interface. Prefer the supported native CLI for reproducible batch slicing/settings where its installed help supports the task; use the native UI for inspection and functions not available through CLI. Existing authorized automation may drive either. Do not substitute OrcaSlicer or install a community MCP bridge without a task-specific reason and the required authorization.

Inspect current CLI help and locally available official profiles; do not assume flags from another version. Resolve inherited presets using supported behavior before invoking operations that need complete settings. Retain printer/nozzle, filament and process identities plus local overrides. A skill or CLI command alone is not evidence that the intended settings were accepted.

Identify the authoritative CAD revision/export and expected manufactured parts. Check the export first by importing it again in a FreeCAD headless run and comparing it with the source (volume, bounding box, part count; see Evidence in `cad-print-workflow`). Import a copy for preparation. Verify scale, units, part count, orientation and intended assembly relationships. The nozzle is 0.4 mm by default; confirm the actual printer setup for the project. STL is unitless; a geometry-only 3MF is not the same as a Bambu project with profiles and settings. STEP import, where supported, does not preserve an editable FreeCAD feature tree.

## Prepare and slice

Work on a saved project copy. Select or confirm intended printer/nozzle/material before optimizing process settings. Propose a material change for agreement when it affects the accepted design. Choose orientation, plate placement, supports, bed adhesion and relevant print parameters for the actual geometry and surface/load priorities.

Compare a small number of meaningful alternatives when tradeoffs matter, retaining the source/settings identity for each result. Change related settings in coherent batches; avoid repeatedly asking about routine settings within agreed goals. Confirm consequential surface-quality, strength, support-removal or cost compromises rather than inventing universal thresholds.

Read [verification and CLI cautions](references/verification.md) for diagnostic interpretation. A long CLI slice is a watched run: `guarding-autonomous-runs` (plugin dv-agent-controller). Capture full stdout/stderr or equivalent diagnostic output, result status and actual artifacts. Do not treat successful file creation or a zero-warning summary as a full printability pass.

## Inspect generated layers

Use actual preview/layer views or supported toolpath evidence, not only a rendered model thumbnail. Inspect critical thin ribs, hooks, gaps, holes, first layers, bridges, overhangs, terminating features and support contact/access. Check both missing features and unintended closure caused by path widening. Confirm removable supports can actually be reached and extracted; automatic support generation alone does not prove this.

For every material finding, record part/location, layer range where available, input revision/profile, evidence, cause hypothesis, and recommended correction. State when preview or a necessary diagnostic is inaccessible: that check is NOT RUN, never PASS. Do not invent screenshots or a passed layer review.

## Print recipe (3 lines)

Every prepared part or plate ends with a short recipe, kept with the project:

1. Material, layer height, walls, infill.
2. Supports and orientation.
3. Why: the one reason that drove these choices (surface, strength direction, support removal, time).

## Classify corrections

- **Settings-only:** adjust the Bambu project and repeat the affected slice and layer checks; CAD evidence stays valid.
- **Local print-driven geometry fix** that preserves the accepted design: edit the source in FreeCAD (a finished solid by the zone method, `freecad-zone-edit`), run the local checks, re-export, re-check the export and re-slice. Never keep a diverging geometry only in the slicer.
- **Significant concept or engineering change:** collect findings and options, get the user's direction as required by `cad-print-workflow`, pause slicing and reopen a dedicated FreeCAD design round. Return only through the CAD-ready gate.

Any geometry change makes the earlier export, slice and layer evidence stale: re-run it or report it as NOT RUN.

Significance is determined by function, visual design, fits, layout, load paths and dependent parts, not a numerical edit-size limit. A user-approved new design goal is a new CAD scope, not an incidental slicing adjustment.

## Deliver preparation, not automatic printing

Return the source/export revision, Bambu project, verified profiles/settings, the print recipe, relevant layer evidence and unresolved findings. Where generated, keep sliced output tied to the exact project inputs. State CAD, slice/layer and physical-validation status separately. Estimates are slicer predictions, not measured physical results.

Do not send a job to a printer, heat/move hardware, change device configuration, activate network credentials or publish files merely because preparation succeeded. Use separate explicit authorization for those actions. This skill requires no printer account, LAN developer mode or hardware connection for offline preparation when the installed application supports it.
