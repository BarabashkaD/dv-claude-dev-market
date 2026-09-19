---
name: dv-freecad-harness-pitfalls
description: Use when building, exporting or measuring a model through the cli-anything-freecad harness — before choosing commands for sketches, pads, pockets, boolean cuts, DXF or SVG export, wires, or volume measurement. Also use when a harness command returned success but the expected file is missing, when an exported file is empty or absent, when a measured volume looks too large, or when a spreadsheet alias is rejected.
---

# FreeCAD harness pitfalls

## Overview

Several `cli-anything-freecad` commands **return a success response and produce nothing**. The harness's own reference documents the happy path; it does not record which paths are silent no-ops.

**Core principle: in this harness, a success response is not evidence that anything was written. Check the artefact.**

Every entry below was verified by direct observation — command run, response captured, filesystem checked. Each lists what to do instead.

## Quick reference

| You want | Documented command | What actually happens | Use instead |
|---|---|---|---|
| A flat part with cut-outs | `sketch new` + `body pad` / `body pocket` | Reports success. Realises nothing. No export file is created at all. | Primitives + booleans in a recipe, executed under `freecadcmd` (below) |
| A boolean cut | `part boolean cut A B` | Recorded, then **never rendered** by `export render` — it reads a `boolean_ops` key that `part boolean` does not populate. Part generation emits `# WARNING: Unknown part type 'cut'` | Execute the recipe yourself under `freecadcmd` |
| A DXF or SVG cut file | `export render out.dxf --preset dxf` (or `--preset svg`) | Silently writes nothing | Write the file yourself from the polygons you already have |
| A drawing | `techdraw export-svg` / `techdraw export-pdf` | Returns success JSON, writes nothing | As above — no 2D export path in this harness works |
| A part's volume | `measure volume <i>` | Returns the **bounding box** for wedge primitives when `deferred: false` — observed 648 against a true 522, **+24.1 %**. Returns `null` for booleans. | Measure on realised OCC solids only |
| A closed profile | `part wire --points "x,y,z;..."` | `--points` is rejected as a flag; points are **positional**. The reference is wrong. | Pass positionally; but see the next row |
| A solid from a profile | `part wire` + `part extrude` | Produces a non-solid. Exported STEP contained 1 CARTESIAN_POINT and **0 faces** | Build from `part add box` primitives and boolean them |
| A named spreadsheet cell | `spreadsheet set-alias 0 A1 T` | Refuses the aliases `T` and `Z1` | Use `T_`, `Z1_`. Other names pass verbatim |

`part add box` works correctly — a plain box exported 6 faces and volume exactly 900, which is how the harness was confirmed functional while the routes above were not.

## What works

Build a **recipe** — a JSON description of primitives, boolean operations and placements — then execute it in a script run under `freecadcmd`, which has the full API and does realise booleans:

```
stage 1   drive cli-anything-freecad  ->  recipe.json   (document, spreadsheet, primitives, placements)
stage 2   freecadcmd realise.py       ->  .fcstd / .step / .stl  + measured volumes
stage 3   your own writer             ->  .dxf / .svg from the same verified polygons
```

Stage 2 exists because the harness's renderer cannot realise the boolean tree stage 1 recorded. Stage 3 exists because no 2D export path works. Keep the polygons as the single source of truth for both the solids and the cut files, so the two cannot drift.

## Verify you actually got output

Because success responses are unreliable, assert on the artefact rather than the exit status:

- **File exists and is non-trivial in size.** A 0-byte or absent file after a success response is the normal failure here.
- **Read the file back and count entities.** For a DXF, count closed polylines and check it equals the parts plus their holes. A file that parses but contains one entity is a failure that passes a smoke test.
- **Compare measured volume against `polygon area × thickness`.** On realised solids this should agree to ~0.00 %. A deviation means the recipe and the polygons disagree — fix the recipe, not the tolerance.
- **Check the solid is a solid.** Count faces; a profile that extruded into a point reports 0.

Make these assertions part of the build, not a one-off check. Two separate export paths in this harness have reported success while writing nothing, so "it worked last time" is not evidence.

## Common mistakes

**Trusting the success response.** The single most expensive habit. Every no-op above returns something that reads like success.

**Measuring volume on primitives.** The bounding-box substitution is silent and inflates by ~24 % on wedges — big enough to matter, small enough to look like a modelling difference rather than a measurement artefact.

**Reaching for sketch/pad because it is the idiomatic FreeCAD workflow.** It is the right answer in FreeCAD proper and the wrong answer through this harness.

**Backgrounding a long build inside a subagent.** Realising a recipe takes a couple of minutes; agents that background it and wait for a notification have stalled indefinitely. Run it in the foreground.

## Scope

Verified against the `cli-anything-freecad` harness (258 commands) with FreeCAD 1.1.1 on macOS, September 2026, while building a 29-part laser-cut assembly. If a path listed here starts working, delete its row — a stale warning costs as much as a missing one.
