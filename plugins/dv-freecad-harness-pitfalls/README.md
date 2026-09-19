# dv-freecad-harness-pitfalls

Companion reference for the `cli-anything-freecad` harness.

Several of the harness's 258 documented commands **return a success response
and produce nothing**. The harness reference documents the happy path; it does
not record which paths are silent no-ops. An agent reading only that reference
will confidently recommend three of them for a routine flat-pack workflow.

This skill records the ones verified by direct observation — command run,
response captured, filesystem checked — each with the working alternative:

| area | documented command | reality |
|---|---|---|
| parts with cut-outs | `sketch new` + `body pad` / `body pocket` | success, realises nothing |
| boolean cuts | `part boolean cut` | recorded, never rendered by `export render` |
| DXF / SVG export | `export render --preset dxf` / `svg` | writes nothing |
| drawings | `techdraw export-svg` / `export-pdf` | success JSON, no file |
| volume | `measure volume` | bounding box for primitives (+24.1% observed), `null` for booleans |
| profiles | `part wire` + `part extrude` | non-solid: 0 faces |
| named cells | `spreadsheet set-alias ... T` | refuses `T` and `Z1` |

Plus the three-stage pipeline that does work: drive the harness to a recipe,
realise it under `freecadcmd` (which executes booleans), and write the cut
files yourself from the same verified polygons.

## Provenance

Verified against FreeCAD 1.1.1 on macOS, September 2026, while building a
29-part laser-cut plywood assembly.

Written test-first, per `superpowers:writing-skills`. The baseline: an agent
asked to advise a greenfield flat-pack project, with the harness reference
available and no prior project to consult, recommended the broken path for
**all three** of building parts, exporting DXF, and checking volumes. With this
skill loaded, the same prompt produced the correct answer for all three.

See `skills/dv-freecad-harness-pitfalls/SKILL.md`.
